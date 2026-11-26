"""Site checks: the top menu (홈·소개·저널) is on every page, the generated pages are up to date,
the CSS is cache-busted, the copy avoids forbidden terms, and the privacy / terms pages exist in ko·en
and are linked from the footer of every page. Run: python3 -m unittest discover -s tests"""
import importlib.util
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

# 약관·개인정보 페이지는 법적 문구라 결제·서버 같은 말을 쓴다 — 금칙어 검사에서 뺀다(메뉴·캐시버스팅·생성본 검사는 같이 본다).
LEGAL_PAGES = [
    "privacy/index.html", "terms/index.html", "en/privacy/index.html", "en/terms/index.html",
]
# 금칙어 검사 대상 = 생성되는 모든 쪽(고정 쪽 + 발행된 저널 글 쪽) — 글이 늘어도 자동으로 따라 들어간다.
PAGES = [file for file, _ in build.public_pages() if file not in LEGAL_PAGES]
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
                f"{base}journal/dev-start/index.html": build.page_post(lang, "dev-start"),
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
        r'<meta property="og:image" content="https://mongsil\.ipe\.rest/assets/img/og-share\.png">',
        r'<meta property="og:image:width" content="1200">',
        r'<meta property="og:image:height" content="630">',
        r'<meta name="twitter:card" content="summary_large_image">',
        r'<meta name="theme-color" content="#fff6f0">',
    ]

    def test_every_page_has_title_description_canonical_hreflang_og(self):
        for rel in self.ALL:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for pattern in self.HEAD_TAGS:
                with self.subTest(page=rel, tag=pattern):
                    self.assertRegex(text, pattern)
            site_name = build.STR[lang_of(rel)]["site_title"]
            with self.subTest(page=rel, tag="og:site_name"):
                self.assertIn(f'<meta property="og:site_name" content="{site_name}">', text)

    def test_og_image_file_exists(self):
        for rel in self.ALL:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                image_url = re.search(
                    r'<meta property="og:image" content="https://mongsil\.ipe\.rest(/assets/img/[^"]+)">', text,
                )
                self.assertIsNotNone(image_url, "og:image URL missing")
                path = ROOT / image_url.group(1).lstrip("/")
                self.assertEqual(path.suffix, ".png")
                self.assertTrue(path.is_file(), path)

    def test_share_png_dimensions_and_size(self):
        png = (ROOT / "assets/img/og-share.png").read_bytes()
        self.assertLess(len(png), 300_000)
        self.assertEqual(png[:16], b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        self.assertEqual(struct.unpack(">II", png[16:24]), (1200, 630))

    def test_no_noindex_anywhere(self):
        for rel in self.ALL:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8").lower()
                self.assertNotIn("noindex", text)
                self.assertNotIn("nofollow", text)

    def test_sitemap_lists_all_pages_with_alternates(self):
        import xml.etree.ElementTree as ET
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        root_el = ET.parse(ROOT / "sitemap.xml").getroot()
        urls = root_el.findall("s:url", ns)
        self.assertEqual(len(urls), len(build.public_pages()))
        self.assertGreaterEqual(len(urls), 12)  # 고정 쪽 12개 + 저널 글 쪽
        locs = {u.find("s:loc", ns).text for u in urls}
        expected = {build.SITE + path for _, path in build.public_pages()}
        self.assertEqual(locs, expected)
        self.assertEqual(len(expected), len(urls))
        for u in urls:
            hreflangs = {l.get("hreflang") for l in u.findall("x:link", ns)}
            with self.subTest(loc=u.find("s:loc", ns).text):
                self.assertEqual(hreflangs, {"ko", "en", "x-default"})

    def test_sitemap_matches_the_page_files(self):
        # 시트맵의 URL 은 실제 생성 파일과 같은 쪽을 가리킨다(저널 글이 늘면 함께 늘어난다).
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
        self.assertEqual(len(expected_by_file), len(build.public_pages()))
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
                self.assertIn('<meta property="og:image" content="https://mongsil.ipe.rest/assets/img/og-share.png">', text)
        for rel in ("index.html", "en/index.html"):
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn(f'src="/assets/img/hero.svg?v={build.CSS_V}"', text)



@unittest.skipIf(os.environ.get("MONGSIL_NESTED"), "발행 스크립트가 check.sh 를 돌리는 중 — 발행 시험은 건너뜀(재귀 방지)")
class PublisherTest(unittest.TestCase):
    """ops/publish_next.py 를 시험한다. 쪽마다 임시 레포 + 임시 bare origin 을 새로 만든다.
    실제 레포·큐·네트워크는 건드리지 않고, push 는 MONGSIL_PUSH=1 일 때만 임시 origin 으로 간다."""

    SLUG = "publisher-test-post"
    QUEUE_ITEM = f"01-{SLUG}"
    DATE, TIME = "2026-11-20", "14:30"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mongsil-pub-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origin = self.tmp / "origin.git"
        self.repo = self.tmp / "repo"
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__", ".published"))
        self.git(self.repo, "init", "-q", "-b", "main")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        self.git(self.repo, "config", "user.name", "test")
        self.git(self.repo, "add", "-A")
        self.git(self.repo, "commit", "-q", "-m", "base")
        self.git(self.repo, "remote", "add", "origin", str(self.origin))
        self.git(self.repo, "push", "-q", "origin", "main")

    @staticmethod
    def git(cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}).stdout.strip()

    def fresh_queue(self, name="q"):
        q = self.tmp / name
        shutil.copytree(ROOT / "ops" / "queue_seed", q)
        # The seed has already been published on the real site. Test a new URL.
        (q / "01-how-to-care-for-mongsil").rename(q / self.QUEUE_ITEM)
        return q

    def publish(self, queue, *extra, push=None):
        env = {k: v for k, v in os.environ.items() if k != "MONGSIL_PUSH"}
        if push is not None:
            env["MONGSIL_PUSH"] = push
        return subprocess.run(
            [sys.executable, "ops/publish_next.py", "--date", self.DATE, "--time", self.TIME,
             "--queue", str(queue), *extra],
            cwd=self.repo, text=True, capture_output=True, env=env)

    def commits(self):
        return int(self.git(self.repo, "rev-list", "--count", "HEAD"))

    def origin_main(self):
        return self.git(self.origin, "rev-parse", "main")

    def status(self):
        return self.git(self.repo, "status", "--porcelain")

    def test_publish_creates_post_list_and_sitemap_entry(self):
        q = self.fresh_queue()
        before = self.commits()
        r = self.publish(q)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.commits(), before + 1)
        for rel in (f"content/journal/{self.SLUG}/ko.md", f"content/journal/{self.SLUG}/en.md",
                    f"journal/{self.SLUG}/index.html", f"en/journal/{self.SLUG}/index.html"):
            self.assertTrue((self.repo / rel).is_file(), rel)
        ko_src = (self.repo / f"content/journal/{self.SLUG}/ko.md").read_text(encoding="utf-8")
        self.assertIn("date: 2026-11-20", ko_src)
        self.assertIn('time: "14:30"', ko_src)
        self.assertIn(f"journal/{self.SLUG}/", (self.repo / "journal/index.html").read_text(encoding="utf-8"))
        self.assertIn(f"en/journal/{self.SLUG}/", (self.repo / "en/journal/index.html").read_text(encoding="utf-8"))
        self.assertIn(f"journal/{self.SLUG}/", (self.repo / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertFalse((q / self.QUEUE_ITEM).exists())
        self.assertTrue((q / ".published" / self.QUEUE_ITEM / "ko.md").is_file())
        self.assertEqual(self.status(), "")

    def test_empty_queue_is_noop_with_stock_alert(self):
        q = self.tmp / "q-empty"
        q.mkdir()
        before = self.commits()
        r = self.publish(q)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("STOCK_ALERT", r.stderr)
        self.assertEqual(self.commits(), before)

    def test_dry_run_writes_nothing(self):
        q = self.fresh_queue()
        before = self.commits()
        r = self.publish(q, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[dry-run] 예정 발행: 2026-11-20 14:30 KST", r.stdout)
        self.assertEqual(self.commits(), before)
        self.assertEqual(self.status(), "")
        self.assertTrue((q / self.QUEUE_ITEM / "ko.md").is_file())
        self.assertFalse((q / ".published").exists())

    def test_dirty_tree_exits_4_and_keeps_queue(self):
        q = self.fresh_queue()
        (self.repo / "stray.txt").write_text("x\n", encoding="utf-8")
        before = self.commits()
        r = self.publish(q)
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertEqual(self.commits(), before)
        self.assertTrue((q / self.QUEUE_ITEM).is_dir())
        self.assertFalse((q / ".published").exists())
        self.assertFalse((self.repo / "content" / "journal" / self.SLUG).exists())

    def test_check_failure_exits_5_and_commits_nothing(self):
        # 금칙어(Firebase)를 넣으면 check.sh 의 금칙어 시험이 새 저널 쪽에서 실패해야 한다.
        q = self.fresh_queue()
        en = q / self.QUEUE_ITEM / "en.md"
        en.write_text(en.read_text(encoding="utf-8") + "\nWe use Firebase here.\n", encoding="utf-8")
        before = self.commits()
        r = self.publish(q)
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertEqual(self.commits(), before)
        self.assertEqual(self.status(), "")
        self.assertFalse((self.repo / "content" / "journal" / self.SLUG).exists())
        self.assertFalse((self.repo / "journal" / self.SLUG).exists())
        self.assertTrue((q / self.QUEUE_ITEM).is_dir())
        self.assertFalse((q / ".published").exists())

    def test_pull_failure_exits_7_and_commits_nothing(self):
        # 로컬만 앞서고 origin 도 따로 앞선 상태(갈라짐) → pull --ff-only 가 실패해야 한다.
        self.git(self.repo, "commit", "-q", "--allow-empty", "-m", "local only")
        other = self.tmp / "other"
        self.git(self.tmp, "clone", "-q", str(self.origin), str(other))
        self.git(other, "config", "user.email", "test@example.invalid")
        self.git(other, "config", "user.name", "test")
        (other / "remote.txt").write_text("remote\n", encoding="utf-8")
        self.git(other, "add", "-A")
        self.git(other, "commit", "-q", "-m", "remote only")
        self.git(other, "push", "-q", "origin", "main")
        q = self.fresh_queue()
        before = self.commits()
        r = self.publish(q)
        self.assertEqual(r.returncode, 7, r.stdout + r.stderr)
        self.assertEqual(self.commits(), before)
        self.assertTrue((q / self.QUEUE_ITEM).is_dir())
        self.assertFalse((self.repo / "content" / "journal" / self.SLUG).exists())

    def test_no_push_when_env_unset(self):
        q = self.fresh_queue()
        base = self.origin_main()
        r = self.publish(q)  # MONGSIL_PUSH 를 빼고 돌린다
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.origin_main(), base)
        self.assertNotIn("PUSH 완료", r.stdout)
        self.assertNotIn("PUSH", r.stderr)

    def test_push_to_origin_when_enabled(self):
        q = self.fresh_queue()
        r = self.publish(q, push="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PUSH 완료", r.stdout)
        self.assertEqual(self.origin_main(), self.git(self.repo, "rev-parse", "HEAD"))

    def test_push_rejection_keeps_the_publish(self):
        hook = self.origin / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho rejected-by-test >&2\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        q = self.fresh_queue()
        base = self.origin_main()
        before = self.commits()
        r = self.publish(q, push="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PUSH 거절", r.stderr)
        self.assertEqual(self.origin_main(), base)
        self.assertEqual(self.commits(), before + 1)
        self.assertTrue((q / ".published" / self.QUEUE_ITEM).is_dir())
        self.assertFalse((q / self.QUEUE_ITEM).exists())


def load_gate():
    spec = importlib.util.spec_from_file_location("journal_gate", ROOT / "ops" / "journal_gate.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


class GateTest(unittest.TestCase):
    """ops/journal_gate.py: 슬롯 시각 범위, 하루 한 번, 실패하면 다음 틱에 재시도.
    임시 큐 폴더와 가짜 발행기만 쓴다(실제 발행·git·~/.ipe 는 건드리지 않는다)."""

    KST = ZoneInfo("Asia/Seoul")

    def setUp(self):
        self.gate = load_gate()
        self.queue = tempfile.mkdtemp(prefix="mongsil-gate-")
        self.addCleanup(shutil.rmtree, self.queue, True)
        self.slot_path = os.path.join(self.queue, "slot.json")
        self.calls = []

    def at(self, hhmm):
        h, m = map(int, hhmm.split(":"))
        return datetime(2026, 11, 20, h, m, tzinfo=self.KST)

    def seed_slot(self, time):
        self.gate.save(self.slot_path, {"date": "2026-11-20", "time": time,
                                        "prev_date": None, "prev_time": None, "published": False})

    def tick(self, hhmm, results):
        results = list(results)

        def fake(date, hhmm_slot, queue):
            self.calls.append((date, hhmm_slot))
            return results.pop(0) if results else True

        return self.gate.run(self.at(hhmm), self.queue, rng=random.Random(1), publish=fake)

    def slot(self):
        return self.gate.load(self.slot_path)

    def test_picks_times_within_12_00_to_17_44(self):
        rng = random.Random(7)
        prev = None
        for _ in range(500):
            t = self.gate.pick_time(prev, rng)
            self.assertTrue(self.gate.valid_time(t), t)
            self.assertTrue("12:00" <= t <= "17:44", t)
            if prev:
                self.assertNotEqual(t[:2], prev[:2])  # 어제와 다른 시(hour)
            prev = t

    def test_valid_time_bounds(self):
        for t in ("12:00", "17:44"):
            self.assertTrue(self.gate.valid_time(t), t)
        for t in ("11:59", "17:45", "17:59", "18:00", "18:15", "99:99", "9:05", "12:60"):
            self.assertFalse(self.gate.valid_time(t), t)

    def test_waits_until_slot_time(self):
        self.seed_slot("12:30")
        self.assertEqual(self.tick("12:00", []), "wait")
        self.assertEqual(self.calls, [])

    def test_failed_publish_is_retried_on_a_later_tick_and_only_once_a_day(self):
        self.seed_slot("12:00")
        self.assertEqual(self.tick("12:00", [False]), "failed")
        self.assertFalse(self.slot()["published"])
        self.assertEqual(self.tick("12:15", [True]), "published")
        self.assertTrue(self.slot()["published"])
        self.assertEqual(self.tick("12:30", []), "skip")
        self.assertEqual(self.tick("13:00", []), "skip")
        # 두 번 다 같은 슬롯 시각(12:00)으로 발행을 부른다 — 틱 시각(12:15)으로 찍히지 않는다.
        self.assertEqual(self.calls, [("2026-11-20", "12:00"), ("2026-11-20", "12:00")])


if __name__ == "__main__":
    unittest.main()
