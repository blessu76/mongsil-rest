"""저널의 프런트매터와 Markdown 본문을 읽고 렌더링한다."""
import html
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from ipe_web_kit import journal, languages  # noqa: E402

ORIGINALS = ("ko", "en")


def parse(text):
    """Split `---` front matter (flat `key: value`, optional quotes) from the body. Returns (meta, body)."""
    m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not m:
        raise ValueError("missing front matter")
    meta = {}
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, m.group(2).strip() + "\n"


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', s)
    return s


def render(body):
    out, para, lst = [], [], None

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None

    for line in body.split("\n"):
        s = line.rstrip()
        mh = re.match(r"(#{2,3})\s+(.*)", s)
        mu = re.match(r"-\s+(.*)", s)
        mo = re.match(r"\d+\.\s+(.*)", s)
        if not s:
            flush_para(); flush_list()
        elif mh:
            flush_para(); flush_list()
            n = len(mh.group(1))
            out.append(f"<h{n}>{inline(mh.group(2))}</h{n}>")
        elif mu or mo:
            flush_para()
            tag = "ul" if mu else "ol"
            if lst and lst[0] != tag:
                flush_list()
            lst = lst or (tag, [])
            lst[1].append((mu or mo).group(1))
        else:
            flush_list()
            para.append(s.strip())
    flush_para(); flush_list()
    return "\n".join(out)


def read_editions(folder):
    """기존 원문 두 편 또는 Iris 검수를 마친 12개 언어판의 원문·정보·본문을 읽는다."""
    editions = {}
    for path in sorted(Path(folder).glob("*.md")):
        lang = path.stem
        if lang not in languages.SUPPORTED:
            raise ValueError(f"지원하지 않는 저널 언어판: {path}")
        text = path.read_text(encoding="utf-8")
        meta, body = parse(text)
        if not (meta.get("title") and meta.get("desc") and body.strip()):
            raise ValueError(f"저널 제목·설명·본문이 필요합니다: {path}")
        editions[lang] = (text, meta, body)

    if set(editions) != set(ORIGINALS):
        journal.assert_publishable({
            Path(folder).name: {lang: {**meta, "url": f"/{lang}/"} for lang, (_, meta, _) in editions.items()},
        })
    return editions


def load_posts(root):
    """발행된 글과 언어판을 읽는다. 원문의 기존 주소를 유지한다."""
    base = os.path.join(root, "content", "journal")
    posts = {}
    if not os.path.isdir(base):
        return posts
    for slug in sorted(os.listdir(base)):
        d = os.path.join(base, slug)
        if not os.path.isdir(d):
            continue
        if not all(Path(d, f"{lang}.md").is_file() for lang in ORIGINALS):
            print(f"저널 원문이 빠져 제외합니다: content/journal/{slug}", file=sys.stderr)
            continue
        editions = read_editions(d)
        stamps = {(meta.get("date"), meta.get("time")) for _, meta, _ in editions.values()}
        if len(stamps) != 1:
            raise ValueError(f"저널 언어판 발행 시각 불일치: {slug}")
        posts[slug] = {lang: (meta, body) for lang, (_, meta, body) in editions.items()}
    return posts
