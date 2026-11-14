import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from aurora.web import static_site as ss


class ParseTests(unittest.TestCase):
    def test_a_table_is_read_without_the_separator_row(self):
        md = "| a | b |\n| --- | --- |\n| 1 | 2 |\n"
        self.assertEqual(ss.parse_table(md), [["a", "b"], ["1", "2"]])

    def test_text_without_a_table_is_empty(self):
        self.assertEqual(ss.parse_table("هیچ جدولی نیست"), [])

    def test_the_summary_line_is_found(self):
        md = "مقدمه\n21 ابزار بررسی شد · 5 پیشنهاد خرید · سرمایه 29.3% · نقد 70.7%\n"
        self.assertIn("21 ابزار", ss.extract_summary(md) or "")

    def test_no_summary_returns_none(self):
        self.assertIsNone(ss.extract_summary("فقط متن"))


class RenderTests(unittest.TestCase):
    def test_html_in_the_source_is_escaped(self):
        out = ss.render_markdown_lite("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_a_table_becomes_a_real_table(self):
        out = ss.render_markdown_lite("| نماد | وزن |\n| --- | --- |\n| KO | 5.9% |\n")
        self.assertIn("<table>", out)
        self.assertIn("KO", out)

    def test_bullets_become_a_list(self):
        out = ss.render_markdown_lite("- یک\n- دو\n")
        self.assertEqual(out.count("<li>"), 2)

    def test_an_unrecognised_line_still_appears(self):
        out = ss.render_markdown_lite(">>> خط عجیب")
        self.assertIn("خط عجیب", out)

    def test_an_empty_section_says_it_was_not_produced(self):
        out = ss.render_markdown_lite("")
        self.assertIn("تولید نشد", out)

    def test_bold_markdown_becomes_strong(self):
        out = ss.render_markdown_lite("**مهم**")
        self.assertIn("<strong>مهم</strong>", out)


class PageTests(unittest.TestCase):
    def test_the_page_is_rtl_and_self_contained(self):
        page = ss.render_page("t", "s", [("a", "1")], [("بخش", "متن")])
        self.assertIn("dir='rtl'", page)
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)

    def test_every_kpi_appears(self):
        page = ss.render_page("t", "s", [("برچسب", "۴۲")], [])
        self.assertIn("۴۲", page)
        self.assertIn("برچسب", page)


class BuildTests(unittest.TestCase):
    def test_the_site_is_written_and_lists_missing_sources(self):
        with TemporaryDirectory() as tmp:
            built = ss.build_site(tmp, "site/index.html")
            self.assertTrue(built.path.exists())
            self.assertEqual(len(built.missing), 3, "هر سه فایل غایب باید گزارش شوند")

    def test_a_present_source_reaches_the_page(self):
        with TemporaryDirectory() as tmp:
            journal = Path(tmp) / "journal"
            journal.mkdir()
            (journal / "advisory.md").write_text("21 ابزار بررسی شد · 5 پیشنهاد خرید", encoding="utf-8")
            built = ss.build_site(tmp, "site/index.html")
            page = built.path.read_text(encoding="utf-8")
            self.assertIn("21 ابزار", page)
            # the source that exists must not be reported as missing; the other two must
            self.assertNotIn("journal/advisory.md", built.missing)
            self.assertIn("journal/routes.md", built.missing)

    def test_the_build_is_deterministic(self):
        with TemporaryDirectory() as tmp:
            first = ss.build_site(tmp, "site/index.html").path.read_text(encoding="utf-8")
            second = ss.build_site(tmp, "site/index.html").path.read_text(encoding="utf-8")
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
