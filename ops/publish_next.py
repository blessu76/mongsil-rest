#!/usr/bin/env python3
"""큐(~/.ipe/queue/mongsil/NN-slug/)의 맨 앞 글을 발행한다.

순서: 작업 트리 확인 → git pull --ff-only origin main (실패하면 쓰지도 커밋하지도 않는다) → content/journal/<slug>/{ko,en}.md 로
복사하며 date·time(슬롯 시각) 을 찍고 → scripts/build.py → scripts/check.sh → git commit.
기존 한국어·영어 원문 또는 Iris 검수를 마친 12개 언어판을 받는다.
push 는 기본 꺼짐(MONGSIL_PUSH=1 일 때만), commit 뒤 별도 단계로 한다. push 가 거절되거나 실패해도(non-fast-forward·네트워크 등)
발행은 성공으로 보고 큐 폴더를 .published/ 로 옮긴다 — 커밋은 클론에 남고, 로그에 PUSH 거절이 남는다.

--dry-run: 아무것도 쓰지 않는다(파일·git·큐 모두). 첫 글·예정 시각·만들 파일만 보여 준다.
종료 코드: 0 발행(또는 dry-run 성공; push 거절·실패 포함) · 3 큐 비었음(STOCK_ALERT) · 4 작업 트리 불안정 ·
5 build/check 실패 · 6 글 형식 오류 · 7 pull --ff-only 실패(커밋 없음, 큐 그대로).
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import kit_lock  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PUSH_TIMEOUT = 60  # 초. 네트워크가 멎어도 틱이 멈추지 않게 한다.


def next_folder(queue):
    if not os.path.isdir(queue):
        return None
    names = sorted(n for n in os.listdir(queue)
                   if re.fullmatch(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*", n) and os.path.isdir(os.path.join(queue, n)))
    return names[0] if names else None


def stamp(text, date, hhmm):
    """front matter 에서 date·time 을 지우고, 여는 --- 바로 다음에 새로 넣는다."""
    head, sep, rest = text.partition("\n---\n")
    lines = [l for l in head.split("\n") if not l.startswith(("date:", "time:"))]
    return "\n".join([lines[0], f"date: {date}", f'time: "{hhmm}"'] + lines[1:]) + sep + rest


def editions(folder):
    from journal_md import read_editions

    return read_editions(folder)


def sh(*cmd, env=None):
    return subprocess.run(cmd, cwd=REPO, check=True, text=True, capture_output=True, env=env).stdout.strip()


def pull():
    """발행 전에 origin main 을 fast-forward 로만 맞춘다. 되지 않으면(갈라짐·네트워크·시간 초과) False — 호출한 쪽은 발행하지 않는다."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        subprocess.run(["git", "pull", "--ff-only", "origin", "main"], cwd=REPO, check=True, text=True,
                       capture_output=True, timeout=PUSH_TIMEOUT, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"PULL 실패(git pull --ff-only origin main 불가 — 발행·커밋하지 않음, 큐 그대로): "
              f"{(e.stderr or e.stdout or '').strip()}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"PULL 시간 초과({PUSH_TIMEOUT}초 — 발행·커밋하지 않음, 큐 그대로)", file=sys.stderr)
    except OSError as e:
        print(f"PULL 을 실행하지 못함(발행·커밋하지 않음, 큐 그대로): {e}", file=sys.stderr)
    return False


def push():
    """origin main 으로 push. 거절·실패·시간 초과는 로그(stderr)에 분명히 남기고 False — 호출한 쪽은 발행을 실패로 보지 않는다."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO, check=True, text=True,
                       capture_output=True, timeout=PUSH_TIMEOUT, env=env)
        print("PUSH 완료: origin main")
        return True
    except subprocess.CalledProcessError as e:
        print(f"PUSH 거절·실패(발행은 유지, 커밋은 클론에 남음 — origin 이 앞서 있으면 non-fast-forward 로 거절됨): "
              f"{(e.stderr or e.stdout or '').strip()}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"PUSH 시간 초과({PUSH_TIMEOUT}초, 발행은 유지, 커밋은 클론에 남음)", file=sys.stderr)
    except OSError as e:
        print(f"PUSH 를 실행하지 못함(발행은 유지, 커밋은 클론에 남음): {e}", file=sys.stderr)
    return False


def dry_run(name, editions, date, hhmm):
    slug = name.split("-", 1)[1]
    when = f"{date} {hhmm} KST" if hhmm else f"{date} 12:00~17:44 KST 사이 (게이트가 그날 시각을 정한다)"
    print(f"[dry-run] 첫 글: {name} (slug: {slug})")
    for lang, (_, meta, _) in editions.items():
        print(f"[dry-run]   {lang}: {meta['title']}")
    print(f"[dry-run] 예정 발행: {when}")
    print(f"[dry-run] 만들 파일(실행 안 함): content/journal/{slug}/의 원문과 {len(editions)}개 언어별 HTML, "
          "목록·sitemap·llms.txt 갱신")
    print("[dry-run] 아무것도 쓰지 않았다 — git·큐 폴더 그대로")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="발행 날짜 YYYY-MM-DD (KST) — 실제 발행에 필수, dry-run 은 생략하면 오늘")
    ap.add_argument("--time", help="발행 시각 HH:MM (KST) — 실제 발행에 필수, dry-run 은 생략 가능")
    ap.add_argument("--queue", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="쓰지 않고 첫 글·예정 시각·만들 파일만 보여 준다(시험용)")
    a = ap.parse_args()
    name = next_folder(a.queue)
    if not name:
        print("STOCK_ALERT: mongsil 저널 큐가 비었다", file=sys.stderr)
        return 3
    folder = os.path.join(a.queue, name)
    if not a.dry_run:
        if not (a.date and a.time):
            ap.error("실제 발행에는 --date 와 --time 이 필요하다")
        if sh("git", "rev-parse", "--abbrev-ref", "HEAD") != "main" or sh("git", "status", "--porcelain"):
            print("main 브랜치가 아니거나 작업 트리가 깨끗하지 않아 발행하지 않는다", file=sys.stderr)
            return 4
        if not pull():
            print("STOP: origin/main 을 ff-only 로 맞추지 못해 발행하지 않는다(커밋 없음, 큐 그대로)", file=sys.stderr)
            return 7
        kit_lock.ensure_for_publish()
    try:
        texts = editions(folder)
    except (ValueError, OSError, ImportError) as e:
        print(f"글 형식 오류: {e}", file=sys.stderr)
        return 6
    if a.dry_run:
        today = datetime.datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
        return dry_run(name, texts, a.date or today, a.time)

    slug = name.split("-", 1)[1]
    dst = f"content/journal/{slug}"
    pages = [f"{lang + '/' if lang != 'ko' else ''}journal/{slug}" for lang in texts]
    env = {**os.environ, "MONGSIL_NESTED": "1"}  # check.sh 의 시험이 발행 시험을 또 돌리지 않게 한다
    try:
        os.makedirs(os.path.join(REPO, dst), exist_ok=True)
        for lang, (text, _, _) in texts.items():
            with open(os.path.join(REPO, dst, lang + ".md"), "w", encoding="utf-8") as f:
                f.write(stamp(text, a.date, a.time))
        sh("python3", "scripts/build.py")
        sh("bash", "scripts/check.sh", env=env)
        sh("git", "add", "-A")
        sh("git", "commit", "-m", f"저널: {slug} ({a.date} {a.time} KST)")
    except (subprocess.CalledProcessError, OSError) as e:
        print(e, file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print((e.stdout or "") + (e.stderr or ""), file=sys.stderr)
        sh("git", "reset", "--hard", "HEAD")
        sh("git", "clean", "-fd", "--", dst, *pages)
        return 5
    if os.environ.get("MONGSIL_PUSH") == "1":
        push()  # 실패해도 발행은 성공 — 아래에서 큐를 옮긴다.
    done = os.path.join(a.queue, ".published")
    os.makedirs(done, exist_ok=True)
    shutil.move(folder, os.path.join(done, name))
    print(f"published {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
