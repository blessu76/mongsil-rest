"""Site checks: the top menu (홈·소개·저널) is on every page, the generated pages are up to date,
the CSS is cache-busted, and the copy avoids forbidden terms. Run: python3 -m unittest discover -s tests"""
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
MENU = {
    "ko": ["홈", "소개", "저널"],
    "en": ["Home", "About", "Journal"],
}
FORBIDDEN = ["릴리즈", "릴리스", "release notes", "서버", "결제", "몽글몽", "몽실몽", "구매", "IAP", "Firebase"]


def lang_of(rel):
    return "en" if rel.startswith("en/") else "ko"


class SiteTest(unittest.TestCase):
    def test_every_page_has_home_about_journal_menu(self):
        for rel in PAGES:
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
            }
            for rel, text in expect.items():
                with self.subTest(page=rel):
                    self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), text,
                                     "run python3 scripts/build.py")

    def test_css_is_cache_busted(self):
        for rel in PAGES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn(f"/assets/mongsil.css?v={build.CSS_V}", text, rel)

    def test_no_forbidden_terms(self):
        for rel in PAGES:
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            for word in FORBIDDEN:
                with self.subTest(page=rel, word=word):
                    self.assertNotIn(word.lower(), text)


if __name__ == "__main__":
    unittest.main()
