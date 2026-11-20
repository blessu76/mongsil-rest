"""Site checks: the top menu (홈·소개·저널) is on every page, the generated pages are up to date,
the CSS is cache-busted, the copy avoids forbidden terms, and the privacy / terms pages exist in ko·en
and are linked from the footer of every page. Run: python3 -m unittest discover -s tests"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

PAGES = [
    "index.html", "about/index.html", "journal/index.html", "journal/dev-start/index.html",
    "en/index.html", "en/about/index.html", "en/journal/index.html", "en/journal/dev-start/index.html",
]
# 약관·개인정보 페이지는 법적 문구라 결제·서버 같은 말을 쓴다 — 금칙어 검사에서 뺀다(메뉴·캐시버스팅·생성본 검사는 같이 본다).
LEGAL_PAGES = [
    "privacy/index.html", "terms/index.html", "en/privacy/index.html", "en/terms/index.html",
]
MENU = {
    "ko": ["홈", "소개", "저널"],
    "en": ["Home", "About", "Journal"],
}
FORBIDDEN = ["릴리즈", "릴리스", "release notes", "서버", "결제", "몽글몽", "몽실몽", "구매", "IAP", "Firebase"]
ANALYTICS = ["googletagmanager", "gtag(", "gtag/js", "google-analytics", "ga-tag"]  # tags, not the word (the policy says "no analytics")


def lang_of(rel):
    return "en" if rel.startswith("en/") else "ko"


def prefix_of(rel):
    return "/en" if rel.startswith("en/") else ""


class SiteTest(unittest.TestCase):
    def test_every_page_has_home_about_journal_menu(self):
        for rel in PAGES + LEGAL_PAGES:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                nav = re.search(r'<nav aria-label="[^"]*"><ul class="menu">(.*?)</ul></nav>', text, re.S)
                self.assertIsNotNone(nav, "menu missing")
                labels = re.findall(r"<a href=\"[^\"]*\"[^>]*>([^<]+)</a>", nav.group(1))
                self.assertEqual(labels, MENU[lang_of(rel)])

    def test_pages_are_up_to_date_with_build(self):
        for lang in ("ko", "en"):
            base = "" if lang == "ko" else "en/"
            expect = {
                f"{base}index.html": build.page_home(lang),
                f"{base}about/index.html": build.page_about(lang),
                f"{base}journal/index.html": build.page_journal(lang),
                f"{base}journal/dev-start/index.html": build.page_post(lang),
                f"{base}privacy/index.html": build.page_legal(lang, "privacy"),
                f"{base}terms/index.html": build.page_legal(lang, "terms"),
            }
            for rel, text in expect.items():
                with self.subTest(page=rel):
                    self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), text,
                                     "run python3 scripts/build.py")

    def test_css_is_cache_busted(self):
        for rel in PAGES + LEGAL_PAGES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn(f"/assets/mongsil.css?v={build.CSS_V}", text, rel)

    def test_css_keeps_korean_words_together(self):
        css = (ROOT / "assets" / "mongsil.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"word-break:\s*keep-all;")

    def test_no_forbidden_terms(self):
        for rel in PAGES:
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            for word in FORBIDDEN:
                with self.subTest(page=rel, word=word):
                    self.assertNotIn(word.lower(), text)

    def test_legal_pages_exist_in_ko_and_en(self):
        for rel in LEGAL_PAGES:
            with self.subTest(page=rel):
                self.assertTrue((ROOT / rel).is_file(), "page missing")
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn(f'<html lang="{lang_of(rel)}">', text)
                self.assertIn("<h1>", text)
                self.assertIn("ipe.haven@gmail.com", text)

    def test_legal_pages_have_no_analytics(self):
        for rel in LEGAL_PAGES:
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            for word in ANALYTICS:
                with self.subTest(page=rel, word=word):
                    self.assertNotIn(word, text)

    def test_footer_links_privacy_and_terms_on_every_page(self):
        for rel in PAGES + LEGAL_PAGES:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                foot = re.search(r"<footer class=\"foot\">(.*?)</footer>", text, re.S)
                self.assertIsNotNone(foot, "footer missing")
                p = prefix_of(rel)
                self.assertIn(f'href="{p}/privacy/"', foot.group(1))
                self.assertIn(f'href="{p}/terms/"', foot.group(1))

    def test_legal_ko_en_have_same_number_of_sections(self):
        for kind in ("privacy", "terms"):
            ko = (ROOT / kind / "index.html").read_text(encoding="utf-8")
            en = (ROOT / "en" / kind / "index.html").read_text(encoding="utf-8")
            with self.subTest(kind=kind):
                self.assertEqual(len(re.findall(r"<h2>", ko)), len(re.findall(r"<h2>", en)))

    def test_legal_canonical_and_hreflang_pair_up(self):
        for kind in ("privacy", "terms"):
            ko = (ROOT / kind / "index.html").read_text(encoding="utf-8")
            en = (ROOT / "en" / kind / "index.html").read_text(encoding="utf-8")
            with self.subTest(kind=kind):
                ko_canon = re.search(r'<link rel="canonical" href="([^"]+)"', ko).group(1)
                en_canon = re.search(r'<link rel="canonical" href="([^"]+)"', en).group(1)
                ko_hreflang = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', ko))
                en_hreflang = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', en))
                self.assertEqual(ko_canon, ko_hreflang["ko"])
                self.assertEqual(ko_hreflang["en"], en_canon)
                self.assertEqual(en_canon, en_hreflang["en"])
                self.assertEqual(en_hreflang["ko"], ko_canon)

    def test_privacy_has_icloud_and_iap_sections(self):
        ko = (ROOT / "privacy" / "index.html").read_text(encoding="utf-8")
        en = (ROOT / "en" / "privacy" / "index.html").read_text(encoding="utf-8")
        self.assertIn("iCloud", ko)
        self.assertIn("인앱결제", ko)
        self.assertIn("iCloud", en)
        self.assertIn("In-App Purchase", en)

    def test_privacy_section1_does_not_say_device_only(self):
        # §1 는 iCloud 동기화(§2)와 어긋나면 안 된다 — "기기 안에만" / "only on your device" 를 쓰지 않는다.
        ko_s1 = " ".join(build.LEGAL["ko"]["privacy"]["sections"][0][1])
        en_s1 = " ".join(build.LEGAL["en"]["privacy"]["sections"][0][1])
        self.assertNotIn("기기 안에만", ko_s1)
        self.assertNotIn("only on your device", en_s1)

    def test_privacy_section1_states_random_id_sync_fact(self):
        # 무작위 ID 는 iCloud 를 켜면 본인 iCloud 로 동기화될 수 있으므로, §1 은 "iCloud 포함 미전송" 이라고 쓰면 안 된다.
        ko_s1 = " ".join(build.LEGAL["ko"]["privacy"]["sections"][0][1])
        en_s1 = " ".join(build.LEGAL["en"]["privacy"]["sections"][0][1])
        self.assertNotIn("기기 밖(iCloud 포함)", ko_s1)
        self.assertNotIn("not synced to iCloud", en_s1)
        self.assertNotIn("sent off your device", en_s1)
        self.assertIn("ipe 로는 보내지 않", ko_s1)
        self.assertIn("not sent to ipe", en_s1)

    def test_no_external_analytics_script_on_any_page(self):
        # 외부 스크립트(http/https src) 금지 — 인라인 <script> 와 같은 출처 스크립트는 허용.
        for rel in PAGES + LEGAL_PAGES:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                for src in re.findall(r"<script[^>]*\ssrc\s*=\s*[\"']?([^\"'\s>]+)", text, re.I):
                    self.assertFalse(src.lower().startswith(("http://", "https://", "//")), src)


class SeoTest(unittest.TestCase):
    """SEO / GEO: every page has its head tags, nothing is noindexed, the sitemap lists the 12 pages,
    the home pages carry parseable JSON-LD without store facts, and robots.txt / llms.txt exist."""

    ALL = PAGES + LEGAL_PAGES
    HEAD_TAGS = [
        r'<title>[^<]+</title>',
        r'<meta name="description" content="[^"]+">',
        r'<link rel="canonical" href="[^"]+">',
        r'<link rel="alternate" hreflang="ko" href="[^"]+">',
        r'<link rel="alternate" hreflang="en" href="[^"]+">',
        r'<link rel="alternate" hreflang="x-default" href="[^"]+">',
        r'<meta property="og:title" content="[^"]+">',
        r'<meta property="og:description" content="[^"]+">',
        r'<meta property="og:url" content="[^"]+">',
        r'<meta property="og:type" content="website">',
        r'<meta property="og:image" content="https://mongsil\.ipe\.rest/assets/img/[^"]+">',
    ]

    def test_every_page_has_title_description_canonical_hreflang_og(self):
        for rel in self.ALL:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for pattern in self.HEAD_TAGS:
                with self.subTest(page=rel, tag=pattern):
                    self.assertRegex(text, pattern)

    def test_og_image_file_exists(self):
        for rel in self.ALL:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for path in re.findall(r'og:image" content="https://mongsil\.ipe\.rest(/assets/img/[^"]+)"', text):
                with self.subTest(page=rel, image=path):
                    self.assertTrue((ROOT / path.lstrip("/")).is_file())

    def test_no_noindex_anywhere(self):
        for rel in self.ALL:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8").lower()
                self.assertNotIn("noindex", text)
                self.assertNotIn("nofollow", text)

    def test_sitemap_lists_all_12_pages_with_alternates(self):
        import xml.etree.ElementTree as ET
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        root_el = ET.parse(ROOT / "sitemap.xml").getroot()
        urls = root_el.findall("s:url", ns)
        self.assertEqual(len(urls), 12)
        locs = {u.find("s:loc", ns).text for u in urls}
        expected = {build.SITE + path for _, path in build.public_pages()}
        self.assertEqual(locs, expected)
        self.assertEqual(len(expected), 12)
        for u in urls:
            hreflangs = {l.get("hreflang") for l in u.findall("x:link", ns)}
            with self.subTest(loc=u.find("s:loc", ns).text):
                self.assertEqual(hreflangs, {"ko", "en", "x-default"})

    def test_sitemap_matches_the_page_files(self):
        # 시트맵의 URL 12개는 실제 생성 파일 12개와 같은 쪽을 가리킨다.
        for file, path in build.public_pages():
            with self.subTest(file=file):
                self.assertTrue((ROOT / file).is_file())
                self.assertIn(f'<link rel="canonical" href="{build.SITE + path}">',
                              (ROOT / file).read_text(encoding="utf-8"))

    def test_x_default_is_the_ko_url_of_each_page(self):
        # x-default 은 쪽마다 그 쪽의 ko 판 URL 이다(예: /en/privacy/ → /privacy/). 홈 하나로 고정하지 않는다.
        expected_by_file = {}
        for file, path in build.public_pages():
            ko_path = path[len("/en"):] if path.startswith("/en") else path
            expected_by_file[file] = build.SITE + ko_path
        self.assertEqual(len(expected_by_file), 12)
        for file, want in expected_by_file.items():
            with self.subTest(file=file):
                text = (ROOT / file).read_text(encoding="utf-8")
                got = re.search(r'<link rel="alternate" hreflang="x-default" href="([^"]+)">', text).group(1)
                self.assertEqual(got, want)
        # 영어 하위 쪽(홈 제외)이 x-default 로 홈(/)을 가리키지 않는지 — 2쪽 이상 검사한다(영어 홈의 ko 짝은 홈 자신이다).
        en_files = [f for f in expected_by_file if f.startswith("en/") and f != "en/index.html"]
        self.assertGreaterEqual(len(en_files), 2)
        for file in en_files:
            with self.subTest(file=file):
                self.assertNotEqual(expected_by_file[file], build.SITE + "/")
        # 시트맵의 x-default 도 같은 규칙.
        import xml.etree.ElementTree as ET
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        for u in ET.parse(ROOT / "sitemap.xml").getroot().findall("s:url", ns):
            loc = u.find("s:loc", ns).text
            xd = next(l.get("href") for l in u.findall("x:link", ns) if l.get("hreflang") == "x-default")
            ko = next(l.get("href") for l in u.findall("x:link", ns) if l.get("hreflang") == "ko")
            with self.subTest(loc=loc):
                self.assertEqual(xd, ko)

    def test_home_jsonld_parses_and_has_no_store_facts(self):
        import json
        for rel in ("index.html", "en/index.html"):
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                blocks = re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', text, re.S)
                self.assertEqual(len(blocks), 1)
                data = json.loads(blocks[0])
                types = {item["@type"] for item in data["@graph"]}
                self.assertEqual(types, {"WebSite", "VideoGame"})
                game = next(i for i in data["@graph"] if i["@type"] == "VideoGame")
                self.assertEqual(game["gamePlatform"], "iOS")
                self.assertIn("name", game)
                self.assertIn("description", game)
                for banned in ("datePublished", "offers", "aggregateRating", "review", "downloadUrl"):
                    self.assertNotIn(banned, game)
                self.assertNotIn("apps.apple.com", blocks[0])

    def test_robots_txt_points_to_sitemap(self):
        text = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", text)
        self.assertNotRegex(text, r"(?m)^Disallow:\s*/\s*$")
        self.assertIn(f"Sitemap: {build.SITE}/sitemap.xml", text)

    def test_llms_txt_describes_game_and_links_pages(self):
        text = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# "))
        for word in ("몽실이 키우기", "Mongsil", "iOS", "광고 없음"):
            with self.subTest(word=word):
                self.assertIn(word, text)
        # 언어 수 문구는 글자 그대로 고정하지 않는다: 「N개 언어」가 있고 N 은 실제 구현 언어 수(STR)보다 작지 않다.
        counts = [int(n) for n in re.findall(r"(\d+)개 언어", text)]
        self.assertEqual(len(counts), 1)
        self.assertGreaterEqual(counts[0], len(build.STR))
        for _, path in build.public_pages():
            with self.subTest(path=path):
                self.assertIn(build.SITE + path, text)

    def test_generated_seo_files_are_up_to_date(self):
        self.assertEqual((ROOT / "robots.txt").read_text(encoding="utf-8"), build.robots_txt())
        self.assertEqual((ROOT / "sitemap.xml").read_text(encoding="utf-8"), build.sitemap_xml())
        self.assertEqual((ROOT / "llms.txt").read_text(encoding="utf-8"), build.llms_txt())


class PairTest(unittest.TestCase):
    """언어 전환 링크는 쪽별 짝 URL 로 간다(privacy → en/privacy 등), 404 페이지·이미지 캐시버스팅."""

    def _hreflang_pair(self, text):
        return dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', text))

    def test_language_switch_points_to_the_pair_page(self):
        for rel in PAGES + LEGAL_PAGES:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                m = re.search(r'<a class="lang" href="([^"]+)" hreflang="([^"]+)">', text)
                self.assertIsNotNone(m, "language switch missing")
                href, target = m.group(1), m.group(2)
                want_lang = "en" if lang_of(rel) == "ko" else "ko"
                self.assertEqual(target, want_lang)
                pair = self._hreflang_pair(text)[want_lang]
                self.assertEqual(build.SITE + href, pair)

    def test_switch_is_not_fixed_to_the_home_page(self):
        text = (ROOT / "privacy" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<a class="lang" href="/en/privacy/"', text)
        text = (ROOT / "en" / "about" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<a class="lang" href="/about/"', text)

    def test_404_page_exists_is_noindex_and_not_in_sitemap(self):
        path = ROOT / "404.html"
        self.assertTrue(path.is_file(), "404.html missing")
        text = path.read_text(encoding="utf-8")
        self.assertIn('<meta name="robots" content="noindex">', text)
        self.assertNotIn("<link rel=\"canonical\"", text)
        self.assertNotIn("hreflang", text)
        self.assertIn('href="/"', text)
        self.assertIn('href="/en/"', text)
        self.assertIn('lang="ko"', text)
        self.assertIn('lang="en"', text)
        self.assertNotIn("404.html", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertEqual(text, build.page_404())

    def test_404_page_css_and_icon_are_cache_busted(self):
        text = (ROOT / "404.html").read_text(encoding="utf-8")
        self.assertIn(f"/assets/mongsil.css?v={build.CSS_V}", text)
        self.assertIn(f"/assets/img/icon.svg?v={build.CSS_V}", text)

    def test_icon_and_hero_are_cache_busted_but_og_image_is_not(self):
        for rel in PAGES + LEGAL_PAGES:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn(f'href="/assets/img/icon.svg?v={build.CSS_V}"', text)
                self.assertIn(f'src="/assets/img/icon.svg?v={build.CSS_V}"', text)
                self.assertIn('content="https://mongsil.ipe.rest/assets/img/icon.svg">', text)
        for rel in ("index.html", "en/index.html"):
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn(f'src="/assets/img/hero.svg?v={build.CSS_V}"', text)


if __name__ == "__main__":
    unittest.main()
