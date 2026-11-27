#!/usr/bin/env python3
"""몽실이 웹 페이지, 사이트맵과 저널을 생성한다."""
from pathlib import Path
import html
import json
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("MONGSIL_PUSH") == "1":
    import kit_lock

    kit_lock.ensure_for_publish()
import journal_md  # noqa: E402
sys.path.insert(0, str(ROOT / "vendor"))
from ipe_web_kit import languages, langswitch, seo  # noqa: E402

CSS_V = "20261126a"
SITE = "https://mongsil.ipe.rest"
OG_IMAGE = "/assets/img/og-share.png"
OG_WIDTH, OG_HEIGHT = 1200, 630
THEME_COLOR = "#fff6f0"
MAIL = "ipe.haven@gmail.com"
OPERATOR = "Davy Kim (ipe Studio)"

LANGS = languages.SUPPORTED
COPY = {
    lang: json.loads((ROOT / "content" / "site" / f"{lang}.json").read_text(encoding="utf-8"))
    for lang in LANGS
}
NAV = {lang: copy["nav"] for lang, copy in COPY.items()}
STR = {lang: copy["site"] for lang, copy in COPY.items()}
LEGAL = {lang: copy["legal"] for lang, copy in COPY.items()}
LANG_ASSET = {"js": f"/assets/ipe-lang.js?v={langswitch.asset_version()}"}


def prefix(lang):
    return "" if lang == "ko" else f"/{lang}"


def path_language(path):
    first = path.split("/", 2)[1]
    return first if first in LANGS else "ko"


def base_path(path):
    return path[len(prefix(path_language(path))):]


def esc(s):
    return html.escape(s, quote=True)


def editions_for(path):
    parts = base_path(path).strip("/").split("/")
    if len(parts) == 2 and parts[0] == "journal":
        return tuple(lang for lang in LANGS if lang in POSTS[parts[1]])
    return LANGS


def alternates(path):
    base = base_path(path)
    return {lang: SITE + prefix(lang) + base for lang in editions_for(path)}


def head(lang, title, desc, path, og_img=OG_IMAGE, extra=""):
    canonical = SITE + path
    urls = alternates(path)
    alternate_html = seo.alternate_links(urls.items(), x_default=urls["ko"])
    language_scripts = (
        f'<script src="/assets/mongsil-lang.js?v={CSS_V}" defer></script>\n'
        + langswitch.script(LANG_ASSET, redirect=False)  # 루트는 ko 그대로 — 자동 언어 이동은 검색엔진·공유 링크에 불리해 끈다
    )
    og_size = ""
    if og_img == OG_IMAGE:
        og_size = (
            f'<meta property="og:image:width" content="{OG_WIDTH}">\n'
            f'<meta property="og:image:height" content="{OG_HEIGHT}">\n'
        )
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{THEME_COLOR}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{alternate_html}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{esc(STR[lang]['site_title'])}">
<meta property="og:image" content="{SITE}{og_img}">
{og_size}<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/icon.svg?v={CSS_V}" type="image/svg+xml">
<link rel="stylesheet" href="/assets/mongsil.css?v={CSS_V}">
{language_scripts}
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


def header(lang, current, path):
    n = NAV[lang]
    base = base_path(path)
    switch = langswitch.select_html(lang, lambda target: prefix(target) + base, editions_for(path))
    p = prefix(lang)
    items = [
        ("home", f"{p}/" if p else "/", n["home"]),
        ("about", f"{p}/about/", n["about"]),
        ("journal", f"{p}/journal/", n["journal"]),
    ]
    links = "".join(
        '<li><a href="%s"%s>%s</a></li>' % (href, ' aria-current="page"' if key == current else "", esc(label))
        for key, href, label in items
    )
    return f"""<body>
<a class="skip" href="#main">{STR[lang]['skip']}</a>
<header class="top">
  <a class="brand" href="{p + '/' if p else '/'}"><img src="/assets/img/icon.svg?v={CSS_V}" alt="" width="32" height="32"><span>{STR[lang]['site_title']}</span></a>
  <nav aria-label="{STR[lang]['menu_label']}"><ul class="menu">{links}</ul></nav>
  {switch}
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


# 저널은 발행일이 있는 언어판만 올린다. 기존 한국어·영어 원문을 다른 언어 목록에서도 읽을 수 있다.
POSTS = journal_md.load_posts(ROOT)
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]


def date_label(lang, iso):
    y, m, d = (int(x) for x in iso.split("-"))
    if lang == "ko":
        return f"{y}년 {m}월 {d}일"
    if lang == "en":
        return f"{MONTHS_EN[m - 1]} {d}, {y}"
    if lang in ("ja", "zh-Hant"):
        return f"{y}年{m}月{d}日"
    if lang in ("de", "tr"):
        return f"{d:02d}.{m:02d}.{y}"
    return f"{d:02d}/{m:02d}/{y}"  # es fr id pt-BR th vi


def post_list(lang):
    """날짜·시각 내림차순으로 언어판을 반환한다. 번역이 없으면 영어판을 연결한다."""
    items = []
    for slug, editions in POSTS.items():
        edition = lang if lang in editions else "en"
        meta, _ = editions[edition]
        if meta.get("date"):
            items.append((slug, edition, meta))
    return sorted(items, key=lambda item: (item[2]["date"], item[2].get("time", "")), reverse=True)


def post_link(lang, slug, edition, meta):
    hint = f' <small>{esc(STR[lang]["original"])}</small>' if edition != lang else ""
    return (
        f'<a href="{prefix(edition)}/journal/{slug}/" lang="{edition}">{esc(meta["title"])}</a>'
        f'{hint} <time class="date" datetime="{meta["date"]}">{date_label(lang, meta["date"])}</time>'
    )


def latest_line(lang):
    items = post_list(lang)
    return f"<p>{post_link(lang, *items[0])}</p>" if items else ""


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
  <img class="hero-img" src="/assets/img/hero.svg?v={CSS_V}" alt="" width="200" height="200">
</section>
<section class="block">
  <h2>{s['points_h2']}</h2>
  <ul class="cards">{cards}</ul>
</section>
<section class="block">
  <h2>{s['journal_h2']}</h2>
  {latest_line(lang)}
  <p><a class="btn ghost" href="{p}/journal/">{s['journal_more']}</a></p>
</section>
</main>
"""
    path = (p + "/") if p else "/"
    return head(lang, s["home_title"], s["home_desc"], path, extra=jsonld_home(lang)) + header(lang, "home", path) + main + footer(lang)


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
    return head(lang, s["about_title"], s["about_desc"], f"{p}/about/") + header(lang, "about", f"{p}/about/") + main + footer(lang)


def page_journal(lang):
    s = STR[lang]
    p = prefix(lang)
    items = "".join(
        f"<li>{post_link(lang, *item)}</li>" for item in post_list(lang)
    )
    main = f"""<main id="main">
<article class="doc">
  <h1>{s['journal_h1']}</h1>
  <p class="lead">{s['journal_sub']}</p>
  <ul class="posts">{items}</ul>
</article>
</main>
"""
    return head(lang, s["journal_title"], s["journal_desc"], f"{p}/journal/") + header(lang, "journal", f"{p}/journal/") + main + footer(lang)


def page_post(lang, slug):
    s = STR[lang]
    p = prefix(lang)
    meta, body = POSTS[slug][lang]
    main = f"""<main id="main">
<article class="doc">
  <p class="date">{date_label(lang, meta['date'])}</p>
  <h1>{esc(meta['title'])}</h1>
  {journal_md.render(body)}
  <p><a href="{p}/journal/">{s['back_journal']}</a></p>
</article>
</main>
"""
    return head(lang, meta["title"] + " — " + s["site_title"], meta["desc"], f"{p}/journal/{slug}/") + header(lang, "journal", f"{p}/journal/{slug}/") + main + footer(lang)


def legal_body(text):
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
        f"<h2>{esc(h)}</h2>{legal_body(paras)}" for h, paras in d["sections"]
    )
    effective = COPY[lang]["effective"]
    eff = effective["format"].format(date=effective["date"], operator=OPERATOR)
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
    return head(lang, f"{d['title']} — {s['site_title']}", d["desc"], path) + header(lang, None, path) + main + footer(lang)


def page_404():
    """사이트 루트 404.html (GitHub Pages 가 쓴다). noindex, canonical·hreflang 없음, sitemap 에 넣지 않는다.
    한국어·영어 짧은 안내와 홈 링크 두 개. 헤더 모양은 다른 쪽과 같다(브랜드 링크만)."""
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>페이지를 찾을 수 없어요 — 몽실이 키우기</title>
<meta name="description" content="몽실이 키우기 페이지를 찾을 수 없어요. 홈으로 돌아가 주세요. · Page not found. Go back to the home page.">
<meta name="robots" content="noindex">
<link rel="icon" href="/assets/img/icon.svg?v={CSS_V}" type="image/svg+xml">
<link rel="stylesheet" href="/assets/mongsil.css?v={CSS_V}">
</head>
<body>
<header class="top">
  <a class="brand" href="/"><img src="/assets/img/icon.svg?v={CSS_V}" alt="" width="32" height="32"><span>{STR['ko']['site_title']}</span></a>
</header>
<main id="main">
<article class="doc">
  <h1>페이지를 찾을 수 없어요 · Page not found</h1>
  <p lang="ko">주소가 바뀌었거나 없는 페이지예요. <a class="btn" href="/">홈으로 가기</a></p>
  <p lang="en">This page doesn't exist or has moved. <a class="btn" href="/en/">Go to home</a></p>
</article>
</main>
</body>
</html>
"""


def write(rel, text):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def renderers():
    for lang in LANGS:
        p = prefix(lang)
        yield f"{p}/", lambda lang=lang: page_home(lang)
        yield f"{p}/about/", lambda lang=lang: page_about(lang)
        yield f"{p}/privacy/", lambda lang=lang: page_legal(lang, "privacy")
        yield f"{p}/terms/", lambda lang=lang: page_legal(lang, "terms")
        yield f"{p}/journal/", lambda lang=lang: page_journal(lang)
        for slug, edition, _ in post_list(lang):
            if edition == lang:
                yield f"{p}/journal/{slug}/", lambda lang=lang, slug=slug: page_post(lang, slug)


def output_path(path):
    return path.lstrip("/") + "index.html"


def public_pages():
    return [(output_path(path), path) for path, _ in renderers()]


def robots_txt():
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"


def sitemap_xml():
    entries = []
    for _, path in public_pages():
        urls = alternates(path)
        links = "".join(
            f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{url}"/>\n'
            for lang, url in [*urls.items(), ("x-default", urls["ko"])]
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
        "> 몽실이 키우기(Mongsil)는 죽지 않는 다마고치류 펫 돌봄 게임입니다.",
        "",
        "- 플랫폼: iOS 앱 (출시 준비 중)",
        "- 만든 곳: ipe() (ipe Studio, 개인 개발자 Davy Kim)",
        "- 광고 없음 · 자체 서버와 별도 계정 없음 · 기기 저장 및 선택적 iCloud 동기화",
        f"- 언어: {len(LANGS)}개 언어",
    ]
    for lang in LANGS:
        site, nav, legal = STR[lang], NAV[lang], LEGAL[lang]
        p = prefix(lang)
        lines += [
            "", f"## {languages.NAMES[lang]}", "",
            f"- [{site['site_title']}]({SITE}{p}/)",
            f"- [{nav['about']}]({SITE}{p}/about/)",
            f"- [{nav['journal']}]({SITE}{p}/journal/)",
            f"- [{legal['privacy_link']}]({SITE}{p}/privacy/)",
            f"- [{legal['terms_link']}]({SITE}{p}/terms/)",
        ]
        lines += [
            f"- [{meta['title']}]({SITE}{p}/journal/{slug}/)"
            for slug, edition, meta in post_list(lang) if edition == lang
        ]
    return "\n".join(lines) + "\n"


def main():
    langswitch.copy_assets(ROOT / "assets")
    for path, render in renderers():
        write(output_path(path), render())
    write("robots.txt", robots_txt())
    write("sitemap.xml", sitemap_xml())
    write("llms.txt", llms_txt())
    write("404.html", page_404())


if __name__ == "__main__":
    main()
