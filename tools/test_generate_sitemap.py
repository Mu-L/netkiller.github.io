#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import generate_sitemap


class LlmsFullGenerationTest(unittest.TestCase):
    def test_llms_full_includes_nested_directories_and_chapter_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CNAME").write_text("example.com\n", encoding="utf-8")
            (root / "index.html").write_text("<title>Home</title>", encoding="utf-8")
            (root / "book").mkdir()
            (root / "book" / "index.html").write_text(
                "<title>Book Index</title>",
                encoding="utf-8",
            )
            (root / "book" / "chapter.html").write_text(
                "<title>Chapter One</title>",
                encoding="utf-8",
            )
            (root / "book" / "nested").mkdir()
            (root / "book" / "nested" / "index.html").write_text(
                "<title>Nested Index</title>",
                encoding="utf-8",
            )
            (root / "book" / "nested" / "deep.html").write_text(
                "<title>Deep Chapter</title>",
                encoding="utf-8",
            )

            old_root = generate_sitemap.REPO_ROOT
            generate_sitemap.REPO_ROOT = root
            try:
                pages = generate_sitemap.collect_pages(include_extra_files=False)
                content = generate_sitemap.build_llms_full("https://example.com", pages)
            finally:
                generate_sitemap.REPO_ROOT = old_root

        self.assertIn("## Directories And Chapters", content)
        self.assertIn("- [book/](https://example.com/book/index.html): Book Index", content)
        self.assertIn("  - [book/chapter.html](https://example.com/book/chapter.html): Chapter One", content)
        self.assertIn("- [book/nested/](https://example.com/book/nested/index.html): Nested Index", content)
        self.assertIn("  - [book/nested/deep.html](https://example.com/book/nested/deep.html): Deep Chapter", content)


if __name__ == "__main__":
    unittest.main()
