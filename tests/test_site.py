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


if __name__ == "__main__":
    unittest.main()
