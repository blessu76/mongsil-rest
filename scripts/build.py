#!/usr/bin/env python3
"""Build the mongsil.ipe.rest pages (stdlib only, Python 3.8+).

Writes, from the repo root:
  /               ko home · /about/ · /journal/ · /journal/dev-start/
  /en/            en home · /en/about/ · /en/journal/ · /en/journal/dev-start/

Every page gets the same top menu: 홈 / 소개 / 저널 (Home / About / Journal).
Terms and privacy pages are NOT built here: the ipe_web_kit has no terms module and its privacy
module describes comment storage, which does not match this app. See README.md.

Run:  python3 scripts/build.py          (rewrites the generated pages)
"""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parent.parent
CSS_V = "20261119b"  # bump with any CSS / asset change (cache busting ?v=)
SITE = "https://mongsil.ipe.rest"

NAV = {
    "ko": {"home": "홈", "about": "소개", "journal": "저널", "switch": "English", "switch_href": "/en/"},
    "en": {"home": "Home", "about": "About", "journal": "Journal", "switch": "한국어", "switch_href": "/"},
}

STR = {
    "ko": {
        "lang": "ko",
        "site_title": "몽실이 키우기",
        "home_title": "몽실이 키우기 — 죽지 않는 펫 돌봄 게임",
        "home_desc": "몽실이 키우기는 죽지 않는 다마고치류 펫 돌봄 게임입니다. 서두르지 않아도 괜찮아요.",
        "hero_h1": "몽실이를 천천히 돌봐요",
        "hero_p": "몽실이 키우기는 죽지 않는 펫 돌봄 게임이에요. 밥을 주고, 씻기고, 함께 놀고, 재워 주면 몽실이가 조금씩 자라요. 며칠 비워 두어도 몽실이는 떠나지 않아요.",
        "hero_soon": "출시 준비 중",
        "points_h2": "이런 게임이에요",
        "points": [
            ("죽음 없는 돌봄", "필요가 채워지지 않아도 몽실이는 잠들 뿐이에요. 벌도, 경고도, 카운트다운도 없어요."),
            ("돌봄이 곧 기록", "어떻게 돌봐 주었는지가 쌓여서 몽실이의 성격과 모습이 정해져요."),
            ("나만의 속도", "하루에 몇 분만 들여다봐도 괜찮아요. 8시간 동안 비워 두어도 손해는 없어요."),
        ],
        "about_link": "소개 더 보기",
        "journal_h2": "최근 소식",
        "journal_more": "저널 전체 보기",
        "about_title": "소개 — 몽실이 키우기",
        "about_desc": "몽실이 키우기가 어떤 게임인지, 왜 만들고 있는지 소개합니다.",
        "about_h1": "소개",
        "about_p": "몽실이 키우기는 ipe()가 만들고 있는 펫 돌봄 게임이에요. 다마고치처럼 펫을 돌보지만, 펫이 죽지 않는다는 점이 다릅니다. 돌봄을 재촉하지 않고, 한 번 놓쳤다고 해서 벌하지 않아요.",
        "about_h2a": "무엇을 하나요",
        "about_list": [
            "밥, 씻기, 놀기, 재우기, 불 켜기, 쓰다듬기로 몽실이를 돌봐요.",
            "알에서 시작해 아기, 어린이, 어른으로 자라요.",
            "돌봄 기록에 따라 몽실이의 성격과 모습이 달라져요.",
            "졸업한 몽실이는 도감에 남아요.",
        ],
        "about_h2b": "광고 없이 만들어요",
        "about_p2": "광고를 보여 주지 않아요. 몽실이 키우기는 앱을 내려받아 바로 시작할 수 있어요.",
        "about_h2c": "지원 언어",
        "about_p3": "한국어와 영어를 먼저 준비하고 있어요. 나머지 언어도 차례로 추가할 예정이에요.",
        "journal_title": "저널 — 몽실이 키우기",
        "journal_desc": "몽실이 키우기 개발 소식을 전합니다.",
        "journal_h1": "저널",
        "journal_sub": "몽실이 키우기를 만들며 적는 소식이에요.",
        "post_title": "개발을 시작했어요",
        "post_desc": "몽실이 키우기 개발을 시작했어요.",
        "post_date": "2026년 11월 19일",
        "post_body": [
            "몽실이 키우기 개발을 시작했어요.",
            "지금은 몽실이가 자라는 과정과 돌봄 방식을 다듬고 있어요. 화면에 무엇이 나올지는 차츰 보여 드릴게요.",
        ],
        "back_journal": "← 저널 목록",
        "footer": "ipe() · 몽실이 키우기",
        "skip": "본문으로 건너뛰기",
        "menu_label": "주 메뉴",
        "lang_label": "언어",
    },
    "en": {
        "lang": "en",
        "site_title": "Mongsil",
        "home_title": "Mongsil — a pet care game where nobody dies",
        "home_desc": "Mongsil is a Tamagotchi-style pet care game where your pet never dies. Take your time.",
        "hero_h1": "Take care of Mongsil, slowly",
        "hero_p": "Mongsil is a pet care game where your pet never dies. Feed, wash, play and put Mongsil to bed, and it grows little by little. Leave it alone for a few days and Mongsil will still be there.",
        "hero_soon": "Coming soon",
        "points_h2": "What it is",
        "points": [
            ("Care without death", "If a need goes unmet, Mongsil just falls asleep. No punishments, no warnings, no countdowns."),
            ("Care becomes a record", "How you care for Mongsil builds up and shapes its personality and look."),
            ("Your own pace", "A few minutes a day is fine. Leave it for 8 hours and you lose nothing."),
        ],
        "about_link": "More about the game",
        "journal_h2": "Latest news",
        "journal_more": "All journal posts",
        "about_title": "About — Mongsil",
        "about_desc": "What Mongsil is and why we are making it.",
        "about_h1": "About",
        "about_p": "Mongsil is a pet care game made by ipe(). You look after a pet like a Tamagotchi, but the pet never dies. The game does not rush you, and missing a day is not punished.",
        "about_h2a": "What you do",
        "about_list": [
            "Feed, wash, play, put to bed, turn on the light and pet Mongsil.",
            "Mongsil starts as an egg and grows into a baby, a child and an adult.",
            "How you care for Mongsil shapes its personality and look.",
            "A graduated Mongsil stays in the collection.",
        ],
        "about_h2b": "Made without ads",
        "about_p2": "There are no ads in Mongsil. You download the app and start right away.",
        "about_h2c": "Languages",
        "about_p3": "English and Korean come first. More languages will be added one by one.",
        "journal_title": "Journal — Mongsil",
        "journal_desc": "Development news from Mongsil.",
        "journal_h1": "Journal",
        "journal_sub": "Notes from making Mongsil.",
        "post_title": "Development has started",
        "post_desc": "We have started developing Mongsil.",
        "post_date": "November 19, 2026",
        "post_body": [
            "We have started developing Mongsil.",
            "For now we are working on how Mongsil grows and how you care for it. We will show more of the screens as they take shape.",
        ],
        "back_journal": "← Back to journal",
        "footer": "ipe() · Mongsil",
        "skip": "Skip to content",
        "menu_label": "Main menu",
        "lang_label": "Language",
    },
}


def prefix(lang):
    return "" if lang == "ko" else "/en"


def esc(s):
    return html.escape(s, quote=True)


def head(lang, title, desc, path, og_img="/assets/img/icon.svg"):
    canonical = SITE + path
    base = path[len("/en"):] if path.startswith("/en") else path  # language-neutral path
    ko_url = SITE + base
    en_url = SITE + "/en" + base
    return f"""<!doctype html>
<html lang="{STR[lang]['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="ko" href="{ko_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{SITE}/">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}{og_img}">
<link rel="icon" href="/assets/img/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/mongsil.css?v={CSS_V}">
</head>
"""


def header(lang, current):
    n = NAV[lang]
    p = prefix(lang)
    items = [
        ("home", f"{p}/" if p else "/", n["home"]),
        ("about", f"{p}/about/", n["about"]),
        ("journal", f"{p}/journal/", n["journal"]),
    ]
    links = "".join(
        '<li><a href="%s"%s>%s</a></li>' % (href, ' aria-current="page"' if key == current else "", label)
        for key, href, label in items
    )
    return f"""<body>
<a class="skip" href="#main">{STR[lang]['skip']}</a>
<header class="top">
  <a class="brand" href="{p + '/' if p else '/'}"><img src="/assets/img/icon.svg" alt="" width="32" height="32"><span>{STR[lang]['site_title']}</span></a>
  <nav aria-label="{STR[lang]['menu_label']}"><ul class="menu">{links}</ul></nav>
  <a class="lang" href="{n['switch_href']}" hreflang="{'en' if lang == 'ko' else 'ko'}">{n['switch']}</a>
</header>
"""


def footer(lang):
    return f"""<footer class="foot"><p>{STR[lang]['footer']}</p></footer>
</body>
</html>
"""


def page_home(lang):
    s = STR[lang]
    p = prefix(lang)
    cards = "".join(
        f'<li class="card"><h3>{esc(t)}</h3><p>{esc(d)}</p></li>' for t, d in s["points"]
    )
    main = f"""<main id="main">
<section class="hero">
  <div class="hero-text">
    <p class="soon">{s['hero_soon']}</p>
    <h1>{s['hero_h1']}</h1>
    <p class="lead">{s['hero_p']}</p>
    <p><a class="btn" href="{p}/about/">{s['about_link']}</a></p>
  </div>
  <img class="hero-img" src="/assets/img/hero.svg" alt="" width="200" height="200">
</section>
<section class="block">
  <h2>{s['points_h2']}</h2>
  <ul class="cards">{cards}</ul>
</section>
<section class="block">
  <h2>{s['journal_h2']}</h2>
  <p><a href="{p}/journal/dev-start/">{s['post_title']}</a> <span class="date">{s['post_date']}</span></p>
  <p><a class="btn ghost" href="{p}/journal/">{s['journal_more']}</a></p>
</section>
</main>
"""
    return head(lang, s["home_title"], s["home_desc"], (p + "/") if p else "/") + header(lang, "home") + main + footer(lang)


def page_about(lang):
    s = STR[lang]
    p = prefix(lang)
    items = "".join(f"<li>{esc(x)}</li>" for x in s["about_list"])
    main = f"""<main id="main">
<article class="doc">
  <h1>{s['about_h1']}</h1>
  <p class="lead">{s['about_p']}</p>
  <h2>{s['about_h2a']}</h2>
  <ul class="bullets">{items}</ul>
  <h2>{s['about_h2b']}</h2>
  <p>{s['about_p2']}</p>
  <h2>{s['about_h2c']}</h2>
  <p>{s['about_p3']}</p>
</article>
</main>
"""
    return head(lang, s["about_title"], s["about_desc"], f"{p}/about/") + header(lang, "about") + main + footer(lang)


def page_journal(lang):
    s = STR[lang]
    p = prefix(lang)
    main = f"""<main id="main">
<article class="doc">
  <h1>{s['journal_h1']}</h1>
  <p class="lead">{s['journal_sub']}</p>
  <ul class="posts">
    <li><a href="{p}/journal/dev-start/">{s['post_title']}</a> <span class="date">{s['post_date']}</span></li>
  </ul>
</article>
</main>
"""
    return head(lang, s["journal_title"], s["journal_desc"], f"{p}/journal/") + header(lang, "journal") + main + footer(lang)


def page_post(lang):
    s = STR[lang]
    p = prefix(lang)
    body = "".join(f"<p>{esc(x)}</p>" for x in s["post_body"])
    main = f"""<main id="main">
<article class="doc">
  <p class="date">{s['post_date']}</p>
  <h1>{s['post_title']}</h1>
  {body}
  <p><a href="{p}/journal/">{s['back_journal']}</a></p>
</article>
</main>
"""
    return head(lang, s["post_title"] + " — " + s["site_title"], s["post_desc"], f"{p}/journal/dev-start/") + header(lang, "journal") + main + footer(lang)


def write(rel, text):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def main():
    for lang in ("ko", "en"):
        base = "" if lang == "ko" else "en/"
        write(f"{base}index.html", page_home(lang))
        write(f"{base}about/index.html", page_about(lang))
        write(f"{base}journal/index.html", page_journal(lang))
        write(f"{base}journal/dev-start/index.html", page_post(lang))


if __name__ == "__main__":
    main()
