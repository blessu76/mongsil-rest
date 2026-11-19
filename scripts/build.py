#!/usr/bin/env python3
"""Build the mongsil.ipe.rest pages (stdlib only, Python 3.8+).

Writes, from the repo root:
  /               ko home · /about/ · /journal/ · /journal/dev-start/ · /privacy/ · /terms/
  /en/            en home · /en/about/ · /en/journal/ · /en/journal/dev-start/ · /en/privacy/ · /en/terms/

Every page gets the same top menu: 홈 / 소개 / 저널 (Home / About / Journal).
The footer on every page links to the privacy policy and terms of use (LEGAL below).
The legal text is the ipe 앱 사이트 기본 문구 (copied from iltonggi-rest content/ko.json · en.json,
with the app facts filled in for Mongsil: no server, no account, no ads, no analytics, local/iCloud data,
Apple in-app purchase). The site has no analytics tag, so the analytics sections are removed.

It also writes robots.txt, sitemap.xml (all 12 pages, hreflang alternates) and llms.txt.
The home pages (ko · en) carry JSON-LD: WebSite + VideoGame. No release date, price, rating or store link
is written, because the app is not on the store yet.

Run:  python3 scripts/build.py          (rewrites the generated pages and the SEO files)
"""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parent.parent
CSS_V = "20261119c"  # bump with any CSS / asset change (cache busting ?v=)
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


MAIL = "ipe.haven@gmail.com"  # contact, same as the other ipe sites (iltonggi)
EFFECTIVE = {"ko": "2026년 11월 19일", "en": "November 19, 2026"}  # 시행일 — first publication date
OPERATOR = "Davy Kim (ipe Studio)"

# 약관·개인정보처리방침 — ipe 앱 사이트 기본 문구 (iltonggi-rest content/*.json 에서 옮김).
# {mail} 은 MAIL 로 바꾼다. 몽실 사실에 맞춰 고친 곳: 분석·쿠키·날씨 절 삭제, iCloud·인앱결제 절 추가.
LEGAL = {
    "ko": {
        "privacy_link": "개인정보처리방침",
        "terms_link": "이용약관",
        "legal_aria": "법적 링크",
        "back_home": "홈",
        "privacy": {
            "title": "개인정보처리방침",
            "desc": "몽실이 키우기 개인정보처리방침 — 앱은 개인정보를 수집하지 않으며, 진행 데이터는 기기 안(iCloud 를 켠 경우 본인 iCloud)에만 저장됩니다.",
            "callout_label": "핵심:",
            "callout": "몽실이 키우기는 이용자의 개인정보를 수집하지 않습니다. 서버·계정·광고·분석 도구가 없습니다.",
            "sections": [
                ("1. 수집하는 정보 — 없음", [
                    "몽실이 키우기(이하 \"앱\")는 개인 개발자 Davy Kim(ipe Studio)이 운영하는 모바일 게임입니다. 앱은 계정·로그인이 없고, 이름·이메일·연락처·위치 등 어떠한 개인정보도 수집하지 않습니다. 앱은 기기마다 무작위 ID 를 하나 만들어 코인 기록을 기기별로 구분하는 데만 씁니다. 이 ID 는 iCloud 를 켠 경우 진행 데이터와 함께 이용자 본인의 iCloud 로 동기화될 수 있지만, ipe 로는 보내지 않으며 ipe 는 어떤 개인정보도 받지 않습니다. 몽실이의 돌봄 기록·설정·도감은 이용자의 기기 안에 저장되며, iCloud 를 켠 경우에 한해 이용자 본인의 iCloud 로 동기화됩니다. ipe 는 이 데이터를 받지 않습니다. 앱을 삭제하면 기기 안의 데이터는 함께 삭제됩니다.",
                    "앱에는 광고, 분석(애널리틱스), 추적 SDK가 포함되어 있지 않습니다.",
                ]),
                ("2. 기기 저장과 iCloud", [
                    "현재 iOS 앱 기준: 진행 데이터는 기기 안에 저장되며, iPhone 에서 iCloud 를 켠 경우에 한해 같은 Apple 계정의 기기끼리 진행 데이터가 이용자 본인의 iCloud 를 통해 동기화됩니다. 이 동기화는 Apple 의 iCloud 로 이루어지며, ipe 서버는 없고 ipe 는 이 데이터를 받지 않습니다.",
                    "다른 플랫폼을 출시하면 이 방침을 갱신합니다.",
                ]),
                ("3. 웹사이트", [
                    "몽실이 키우기 소개 사이트(mongsil.ipe.rest)에는 방문 통계를 모으는 분석 도구가 없습니다. 호스팅은 GitHub Pages이며, 웹사이트에 접속하면 IP 주소 등 접속 기록이 GitHub 호스팅의 서버 로그에 남을 수 있습니다. 당사는 이 로그를 수집하거나 이용하지 않으며, GitHub의 서버 로그 정책이 적용됩니다.",
                ]),
                ("4. 결제", [
                    "앱 안의 유료 상품은 Apple 인앱결제(App Store)로만 판매합니다. 결제 정보(카드 번호·결제 수단 등)는 Apple이 처리하며, 몽실이 키우기와 ipe는 이를 받거나 보관하지 않습니다. 구매 확인과 복원은 Apple 스토어 기록을 기준으로 합니다.",
                ]),
                ("5. 제3자 제공", [
                    "앱은 개인정보를 수집하지 않으므로 제3자에게 제공하거나 판매하는 정보가 없습니다. 앱은 Apple App Store 를 통해 배포되며, 다운로드·결제와 관련된 정보는 Apple의 개인정보 처리방침에 따라 Apple이 처리합니다.",
                ]),
                ("6. 문의·권리 행사", [
                    "개인정보와 관련한 열람·정정·삭제·처리정지 요청이나 문의는 {mail} 으로 보내 주세요. 앱은 보유한 개인정보가 없어, 찾아서 처리할 정보가 없을 수 있습니다.",
                ]),
                ("7. 아동", [
                    "앱은 만 14세 미만 아동을 대상으로 하지 않으며, 어떤 이용자로부터도 개인정보를 수집하지 않습니다.",
                ]),
                ("8. 개인정보 보호책임자", [
                    "성명: Davy Kim (ipe Studio) · 연락처: {mail}",
                ]),
                ("9. 권리 침해 구제", [
                    "- 개인정보분쟁조정위원회: 1833-6972 · kopico.go.kr",
                    "- 개인정보침해신고센터: 118 · privacy.kisa.or.kr",
                    "- 대검찰청 사이버수사과: 1301 · 경찰청 사이버수사국: 182",
                ]),
                ("10. 변경", [
                    "수집 항목이 달라지면(예: 서버·계정·광고·분석 추가) 이 방침을 먼저 갱신하고 시행일을 바꿔 알립니다.",
                ]),
            ],
        },
        "terms": {
            "title": "이용약관",
            "desc": "몽실이 키우기 이용약관.",
            "sections": [
                ("1. 목적", [
                    "이 약관은 Davy Kim(ipe Studio)이 제공하는 모바일 게임 \"몽실이 키우기\"(이하 \"앱\")의 이용 조건을 정합니다.",
                ]),
                ("2. 이용 허락", [
                    "이용자는 앱을 개인적·비상업적 용도로 기기에 설치하여 이용할 수 있습니다. 앱의 소스 코드·이미지·음원 등을 무단으로 복제·배포·역설계하거나 상업적으로 이용할 수 없습니다.",
                ]),
                ("3. 서비스의 성격", [
                    "앱은 인터넷 연결 없이도 동작합니다. 현재 iOS 앱 기준으로 게임 데이터는 이용자의 기기 안에 저장되며, iCloud 를 켠 경우에 한해 본인 iCloud 를 통해 동기화됩니다. 기기 변경·앱 삭제·초기화 시 데이터가 사라질 수 있고, 당사는 이를 복구해 드리지 못할 수 있습니다.",
                ]),
                ("4. 유료 상품", [
                    "앱의 유료 상품은 Apple 인앱결제로 구매합니다. 결제·환불·구매 취소는 Apple 의 정책과 절차를 따르며, 구매한 상품은 같은 Apple 계정으로 복원할 수 있습니다.",
                ]),
                ("5. 변경과 중단", [
                    "당사는 앱의 기능을 개선·변경하거나 제공을 중단할 수 있으며, 중요한 변경은 앱 스토어 설명 또는 이 사이트를 통해 알립니다.",
                ]),
                ("6. 면책", [
                    "앱은 현재 상태 그대로 제공됩니다. 관련 법령이 허용하는 범위에서 당사는 앱 이용으로 인한 간접적·부수적 손해에 대해 책임을 지지 않습니다.",
                ]),
                ("7. 준거법과 문의", [
                    "이 약관은 대한민국 법령에 따릅니다. 문의: {mail}",
                ]),
            ],
        },
    },
    "en": {
        "privacy_link": "Privacy Policy",
        "terms_link": "Terms of Use",
        "legal_aria": "Legal links",
        "back_home": "Home",
        "privacy": {
            "title": "Privacy Policy",
            "desc": "Privacy policy for Mongsil — the app collects no personal information, and your progress is stored only on your device (or in your own iCloud if you turn iCloud on).",
            "callout_label": "In short:",
            "callout": "Mongsil collects no personal information. There is no server, no account, no advertising and no analytics.",
            "sections": [
                ("1. Information we collect — none", [
                    "Mongsil (\"the App\") is a mobile game operated by an individual developer, Davy Kim (ipe Studio). The App has no accounts or sign-in, and it does not collect any personal information such as your name, email, contact details or location. The App creates a random ID for each device and uses it only to tell apart coin records per device. If you turn on iCloud, this ID may sync with your progress data to your own iCloud, but it is not sent to ipe, and ipe receives no personal information. Your care records, settings and collection are stored on your device and, only if you turn on iCloud, synced through your own iCloud. ipe does not receive this data. Deleting the App deletes the data on your device.",
                    "The App contains no advertising, analytics or tracking SDKs.",
                ]),
                ("2. Device storage and iCloud", [
                    "Current iOS App: your progress is stored on your device, and only if you turn on iCloud on an iPhone is progress synced between devices signed in to the same Apple account through your own iCloud. The sync runs on Apple's iCloud; there is no ipe server, and ipe does not receive this data.",
                    "If we release the App on other platforms, we will update this policy.",
                ]),
                ("3. The website", [
                    "The Mongsil website (mongsil.ipe.rest) has no analytics tool that collects visit statistics. The site is hosted on GitHub Pages; when you visit the website, your IP address and other access records may be kept in GitHub Hosting's server logs. We do not collect or use these logs, and GitHub's server-log policies apply.",
                ]),
                ("4. Payments", [
                    "Paid items in the App are sold only through Apple In-App Purchase (App Store). Payment information (such as card numbers and payment methods) is handled by Apple; Mongsil and ipe do not receive or keep it. Purchase checks and restores are based on Apple's store records.",
                ]),
                ("5. Third parties", [
                    "The App collects no personal information, so there is nothing to share with or sell to third parties. The App is distributed through the Apple App Store; information related to downloads and payments is handled by Apple under Apple's privacy policy.",
                ]),
                ("6. Questions and your rights", [
                    "To request access, correction, deletion or suspension of processing of your personal information, or to ask any question, write to {mail}. The App holds no personal information, so there may be nothing we can find to act on.",
                ]),
                ("7. Children", [
                    "The App is not directed to children under 14 (or the minimum age in your region), and it collects no personal information from any user.",
                ]),
                ("8. Privacy officer", [
                    "Name: Davy Kim (ipe Studio) · Contact: {mail}",
                ]),
                ("9. Remedies (Korea)", [
                    "- Personal Information Dispute Mediation Committee: 1833-6972 · kopico.go.kr",
                    "- Personal Information Infringement Report Center: 118 · privacy.kisa.or.kr",
                    "- Supreme Prosecutors' Office Cybercrime Division: 1301 · National Police Agency Cyber Bureau: 182",
                ]),
                ("10. Changes", [
                    "If the App later adds a server, accounts, advertising or analytics that change what is collected, we will update this policy first and change the effective date.",
                ]),
            ],
        },
        "terms": {
            "title": "Terms of Use",
            "desc": "Terms of Use for Mongsil.",
            "sections": [
                ("1. Purpose", [
                    "These terms set out the conditions for using the mobile game \"Mongsil\" (\"the App\"), provided by Davy Kim (ipe Studio).",
                ]),
                ("2. License", [
                    "You may install and use the App on your device for personal, non-commercial purposes. You may not copy, distribute, reverse engineer or commercially exploit the App's source code, images, audio or other content without permission.",
                ]),
                ("3. Nature of the service", [
                    "The App works without an internet connection. Current iOS App: game data is stored on your device, and only if you turn on iCloud is it synced through your own iCloud. Data may be lost if you change devices, delete the App or reset your device, and we may not be able to restore it.",
                ]),
                ("4. Paid items", [
                    "Paid items in the App are purchased through Apple In-App Purchase. Payment, refunds and cancellations follow Apple's policies and procedures, and purchased items can be restored with the same Apple account.",
                ]),
                ("5. Changes and discontinuation", [
                    "We may improve or change the App's features, or stop providing it. Important changes will be announced in the App Store description or on this site.",
                ]),
                ("6. Disclaimer", [
                    "The App is provided as it is. To the extent permitted by law, we are not liable for indirect or incidental damages arising from your use of the App.",
                ]),
                ("7. Governing law and contact", [
                    "These terms are governed by the laws of the Republic of Korea. Contact: {mail}",
                ]),
            ],
        },
    },
}


def prefix(lang):
    return "" if lang == "ko" else "/en"


def esc(s):
    return html.escape(s, quote=True)


def alternates(path):
    """(ko URL, en URL) for a page path — the same pair for ko and en versions of one page."""
    base = path[len("/en"):] if path.startswith("/en") else path  # language-neutral path
    return SITE + base, SITE + "/en" + base


def head(lang, title, desc, path, og_img="/assets/img/icon.svg", extra=""):
    canonical = SITE + path
    ko_url, en_url = alternates(path)
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
{extra}</head>
"""


def jsonld_home(lang):
    """JSON-LD for the home page: WebSite + VideoGame. Facts only — no datePublished, offers, rating or store URL."""
    s = STR[lang]
    p = prefix(lang)
    home = SITE + (p + "/" if p else "/")
    graph = [
        {
            "@type": "WebSite",
            "name": s["site_title"],
            "url": home,
            "inLanguage": lang,
        },
        {
            "@type": "VideoGame",
            "name": s["site_title"],
            "alternateName": "Mongsil" if lang == "ko" else "몽실이 키우기",
            "description": s["home_desc"],
            "genre": "Virtual pet",
            "gamePlatform": "iOS",
            "url": home,
            "inLanguage": lang,
            "publisher": {"@type": "Organization", "name": "ipe()", "url": "https://ipe.rest/"},
        },
    ]
    for item in graph:
        item["@context"] = "https://schema.org"
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    data = data.replace("</", "<\\/")  # never let a string close the script tag
    return f'<script type="application/ld+json">\n{data}\n</script>\n'


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
    p = prefix(lang)
    L = LEGAL[lang]
    return f"""<footer class="foot"><p>{STR[lang]['footer']}</p>
<nav class="foot-links" aria-label="{esc(L['legal_aria'])}"><a href="{p}/privacy/">{esc(L['privacy_link'])}</a> <a href="{p}/terms/">{esc(L['terms_link'])}</a></nav></footer>
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
    return head(lang, s["home_title"], s["home_desc"], (p + "/") if p else "/", extra=jsonld_home(lang)) + header(lang, "home") + main + footer(lang)


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


def legal_body(lang, text):
    """{mail} → mailto link; '- ' lines → a bullet list; everything else → a paragraph."""
    mail = f'<a href="mailto:{MAIL}">{MAIL}</a>'
    out, bullets = [], []

    def flush():
        if bullets:
            out.append('<ul class="bullets">' + "".join(f"<li>{x}</li>" for x in bullets) + "</ul>")
            bullets.clear()

    for line in text:
        if line.startswith("- "):
            bullets.append(esc(line[2:]).replace("{mail}", mail))
        else:
            flush()
            out.append("<p>%s</p>" % esc(line).replace("{mail}", mail))
    flush()
    return "".join(out)


def page_legal(lang, kind):
    s = STR[lang]
    L = LEGAL[lang]
    d = L[kind]
    p = prefix(lang)
    sections = "".join(
        f"<h2>{esc(h)}</h2>{legal_body(lang, paras)}" for h, paras in d["sections"]
    )
    if lang == "ko":
        eff = f"시행일: {EFFECTIVE[lang]} · 운영: {OPERATOR}"
    else:
        eff = f"Effective: {EFFECTIVE[lang]} · Operated by {OPERATOR}"
    lead = ""
    if kind == "privacy":
        lead = f'<p class="lead"><strong>{esc(d["callout_label"])}</strong> {esc(d["callout"])}</p>'
    main = f"""<main id="main">
<article class="doc">
  <h1>{esc(d['title'])}</h1>
  <p class="date">{esc(eff)}</p>
  {lead}
  {sections}
  <p><a href="{p}/">← {esc(L['back_home'])}</a></p>
</article>
</main>
"""
    path = f"{p}/{kind}/"
    return head(lang, f"{d['title']} — {s['site_title']}", d["desc"], path) + header(lang, None) + main + footer(lang)


def write(rel, text):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def public_pages():
    """(output file, URL path) for the 12 generated pages, ko first then en."""
    out = []
    for lang in ("ko", "en"):
        p = prefix(lang)
        base = "" if lang == "ko" else "en/"
        out += [
            (f"{base}index.html", (p + "/") if p else "/"),
            (f"{base}about/index.html", f"{p}/about/"),
            (f"{base}journal/index.html", f"{p}/journal/"),
            (f"{base}journal/dev-start/index.html", f"{p}/journal/dev-start/"),
            (f"{base}privacy/index.html", f"{p}/privacy/"),
            (f"{base}terms/index.html", f"{p}/terms/"),
        ]
    return out


def robots_txt():
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"


def sitemap_xml():
    entries = []
    for _, path in public_pages():
        ko_url, en_url = alternates(path)
        links = (
            f'    <xhtml:link rel="alternate" hreflang="ko" href="{ko_url}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>\n'
        )
        entries.append(f"  <url>\n    <loc>{SITE + path}</loc>\n{links}  </url>\n")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "".join(entries)
        + "</urlset>\n"
    )


def llms_txt():
    lines = [
        "# 몽실이 키우기 (Mongsil)",
        "",
        "> 몽실이 키우기(Mongsil)는 죽지 않는 다마고치류 펫 돌봄 게임입니다. "
        "밥을 주고, 씻기고, 함께 놀고, 재워 주면 몽실이가 자랍니다. 며칠 비워 두어도 몽실이는 떠나지 않습니다.",
        "",
        "- 플랫폼: iOS 앱 (출시 준비 중)",
        "- 만든 곳: ipe() (ipe Studio, 개인 개발자 Davy Kim)",
        "- 광고 없음 · 서버·계정 없음 · 진행 데이터는 기기 안에 저장 (iCloud 를 켠 경우 본인 iCloud 로 동기화)",
        "- 언어: 12개 언어 지원 예정 (한국어·영어 먼저)",
        "",
        "Mongsil (몽실이 키우기) is a Tamagotchi-style pet care game where your pet never dies. "
        "Feed, wash, play and put it to bed, and it grows. Leave it alone for days and it stays. "
        "iOS app, in preparation. No ads, no server, no account.",
        "",
        "## 한국어 페이지",
        f"- [홈]({SITE}/): 게임 소개",
        f"- [소개]({SITE}/about/): 무엇을 하는지, 광고 없이 만드는 이유",
        f"- [저널]({SITE}/journal/): 개발 소식",
        f"- [저널: 개발을 시작했어요]({SITE}/journal/dev-start/)",
        f"- [개인정보처리방침]({SITE}/privacy/)",
        f"- [이용약관]({SITE}/terms/)",
        "",
        "## English pages",
        f"- [Home]({SITE}/en/): game overview",
        f"- [About]({SITE}/en/about/): what you do and why it has no ads",
        f"- [Journal]({SITE}/en/journal/): development news",
        f"- [Journal: Development has started]({SITE}/en/journal/dev-start/)",
        f"- [Privacy Policy]({SITE}/en/privacy/)",
        f"- [Terms of Use]({SITE}/en/terms/)",
        "",
    ]
    return "\n".join(lines)


def main():
    for lang in ("ko", "en"):
        base = "" if lang == "ko" else "en/"
        write(f"{base}index.html", page_home(lang))
        write(f"{base}about/index.html", page_about(lang))
        write(f"{base}journal/index.html", page_journal(lang))
        write(f"{base}journal/dev-start/index.html", page_post(lang))
        write(f"{base}privacy/index.html", page_legal(lang, "privacy"))
        write(f"{base}terms/index.html", page_legal(lang, "terms"))
    write("robots.txt", robots_txt())
    write("sitemap.xml", sitemap_xml())
    write("llms.txt", llms_txt())


if __name__ == "__main__":
    main()
