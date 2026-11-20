#!/usr/bin/env python3
"""오후 랜덤 발행 게이트 — launchd 가 12:00~18:45 KST 동안 15분마다 부른다.

상태: ~/.ipe/queue/mongsil/slot.json = {"date","time","prev_date","prev_time","published","next_date","next_time"}
(IPE_QUEUE_DIR 로 큐 위치를 바꿀 수 있다 — 시험용)
- 슬롯 시각은 12:00~17:44 만 뽑는다. 발행 글에 찍히는 시각도 틱 시각이 아니라 이 슬롯 시각이라,
  15분 틱이 올림해도 글이 18:00 으로 찍히는 일이 없다.
- 오늘 날짜가 아니면 12:00~17:44 중 어제 시각의 '시'와 다른 시각을 새로 뽑는다(이전 값은 prev_* 로).
  단 발행 때 미리 뽑아 둔 next_date(== 오늘)·next_time 이 유효하면 그것을 쓴다(손상된 값은 버리고 새로 뽑는다).
- 지금 >= time 이고 published=false 면 publish_next.py --time <슬롯 시각> 을 돌리고, 성공하면 published=true 를 먼저 저장한다.
  실패하면 published=false 로 남아 그날 다음 틱에 다시 시도한다.
  next_date·next_time(내일 시각)은 그 뒤 최선 노력으로 적는다 — 실패해도 발행 결과는 그대로다.
  발행이 실패하면 next_* 는 건드리지 않는다.
"""
import fcntl
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.environ.get("IPE_QUEUE_DIR") or os.path.expanduser("~/.ipe/queue/mongsil")
HOURS = range(12, 18)  # 12:00 ~ 17:44 (17시는 0~44분만)
LATEST = "17:44"  # 슬롯·찍히는 시각의 상한 — 18:00 이 되지 않게 한다


def pick_time(prev_time, rng=random):
    """12:00~17:44 중 prev_time 의 시(hour)와 다른 시각 'HH:MM'."""
    prev_hour = int(prev_time.split(":")[0]) if prev_time else None
    hours = [h for h in HOURS if h != prev_hour]
    h = rng.choice(hours)
    m = rng.randrange(60) if h < 17 else rng.randrange(45)  # 17시는 17:00~17:44
    return f"{h:02d}:{m:02d}"


def valid_time(t):
    """'HH:MM'(두 자리) 이고 12:00~17:44 사이인 값만 참."""
    if not isinstance(t, str) or not re.fullmatch(r"\d{2}:\d{2}", t):
        return False
    h, m = int(t[:2]), int(t[3:])
    return h in HOURS and m < 60 and "12:00" <= t <= LATEST


def roll(slot, today, rng=random):
    """날짜가 바뀌었으면 슬롯을 굴린다. 같은 날이면 그대로."""
    if slot and slot.get("date") == today:
        return slot
    old = slot or {}
    # 발행 때 미리 뽑아 둔 오늘 시각(next_*)이 있으면 그대로 쓴다 — 어제와 다른 시(hour)는 그때 이미 보장.
    # 손상된 값("99:99", "9:5", 12~17시 밖)이면 버리고 새로 뽑는다.
    if old.get("next_date") == today and valid_time(old.get("next_time")):
        t = old["next_time"]
    else:
        t = pick_time(old.get("time"), rng)
    return {"date": today, "time": t,
            "prev_date": old.get("date"), "prev_time": old.get("time"), "published": False}


def plan_next(slot, today, rng=random):
    """내일 시각을 미리 뽑아 slot 에 next_date·next_time 으로 적는다(확인용·내일 그대로 사용)."""
    tomorrow = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    slot["next_date"] = tomorrow
    slot["next_time"] = pick_time(slot["time"], rng)
    return slot


def due(slot, now_hhmm):
    return (not slot["published"]) and now_hhmm >= slot["time"]


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save(path, slot):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(slot, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def run(now, queue=QUEUE, rng=random, publish=None):
    """한 번 돈다. 반환: 'skip' | 'wait' | 'published' | 'failed'."""
    os.makedirs(queue, exist_ok=True)
    slot_path = os.path.join(queue, "slot.json")
    with open(os.path.join(queue, ".gate.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        today = now.strftime("%Y-%m-%d")
        before = load(slot_path)
        slot = roll(before, today, rng)
        if slot is not before:
            save(slot_path, slot)
        if not due(slot, now.strftime("%H:%M")):
            return "skip" if slot["published"] else "wait"
        # 글에 찍는 시각은 틱 시각(now)이 아니라 슬롯 시각이다 — 15분 틱의 올림으로 18:00 이 찍히지 않게.
        ok = (publish or default_publish)(today, slot["time"], queue)
        if ok:
            # published=true 를 먼저 디스크에 남긴다 — 이후 단계가 실패해도 다음 틱에 같은 날 재발행되지 않는다.
            slot["published"] = True
            save(slot_path, slot)
            # 내일 시각 미리 뽑기는 최선 노력: 실패해도 발행 결과는 그대로 둔다.
            try:
                plan_next(slot, today, rng)
                save(slot_path, slot)
                print(f"next: {slot['next_date']} {slot['next_time']} KST")
            except Exception as e:  # noqa: BLE001 — 로그만 남기고 발행 성공은 유지
                print(f"next 미리 뽑기 실패(발행은 완료): {e}", file=sys.stderr)
            return "published"
        return "failed"


def default_publish(date, hhmm, queue):
    r = subprocess.run([sys.executable, os.path.join(HERE, "publish_next.py"), "--date", date, "--time", hhmm, "--queue", queue])
    return r.returncode == 0


if __name__ == "__main__":
    try:
        print(run(datetime.now(KST)))
    except BlockingIOError:
        print("busy")
