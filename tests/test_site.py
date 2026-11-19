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


if __name__ == "__main__":
    unittest.main()
