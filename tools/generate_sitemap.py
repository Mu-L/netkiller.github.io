#!/usr/bin/env python3

from __future__ import annotations

import gzip
import subprocess
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOMAIN = "www.netkiller.cn"
EXCLUDED_NAMES = {
    "index.nginx-debian.html",
}
EXCLUDED_PREFIXES = (
    "baidu_verify_",
    "google",
)
PUBLIC_EXTRA_FILES = (
    "llms.txt",
    "llms-full.txt",
)


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self) -> str:
        return normalize_text("".join(self.parts))


def read_domain() -> str:
    for candidate in ("CNAME", "CNAME.backup"):
        path = REPO_ROOT / candidate
        if path.exists():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value.removeprefix("https://").removeprefix("http://").rstrip("/")
    return DEFAULT_DOMAIN


def is_public_html(path: Path) -> bool:
    if path.name in EXCLUDED_NAMES:
        return False
    if any(path.name.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return path.suffix.lower() in {".html", ".htm"}


def collect_pages(include_extra_files: bool = True) -> list[Path]:
    pages = [path for path in REPO_ROOT.rglob("*") if path.is_file() and is_public_html(path)]
    if include_extra_files:
        pages.extend(REPO_ROOT / name for name in PUBLIC_EXTRA_FILES if (REPO_ROOT / name).is_file())
    pages.sort(key=lambda path: path.relative_to(REPO_ROOT).as_posix())
    return pages


def git_lastmod_lookup(pages: Iterable[Path]) -> dict[str, str]:
    wanted = {path.relative_to(REPO_ROOT).as_posix() for path in pages}
    if not wanted:
        return {}

    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "log",
                "--name-only",
                "--format=__DATE__%cs",
                "--diff-filter=AM",
                "--",
                ".",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {}

    lastmod: dict[str, str] = {}
    current_date: str | None = None
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("__DATE__"):
            current_date = line.removeprefix("__DATE__")
            continue
        if current_date and line in wanted and line not in lastmod:
            lastmod[line] = current_date
            if len(lastmod) == len(wanted):
                break
    return lastmod


def fallback_lastmod(path: Path) -> str:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return modified.date().isoformat()


def encode_url(base_url: str, path: Path) -> str:
    relative = path.relative_to(REPO_ROOT)
    quoted = "/".join(quote(part) for part in relative.parts)
    return f"{base_url}/{quoted}"


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def markdown_text(value: str) -> str:
    return normalize_text(value).replace("[", "\\[").replace("]", "\\]")


def page_title(path: Path) -> str:
    try:
        parser = TitleParser()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        if parser.title:
            return parser.title
    except OSError:
        pass
    return path.stem


def relative_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def page_link(base_url: str, path: Path) -> str:
    label = markdown_text(relative_label(path))
    title = markdown_text(page_title(path))
    return f"[{label}]({encode_url(base_url, path)}): {title}"


def directory_link(base_url: str, directory: Path, index_page: Path | None) -> str:
    if directory == REPO_ROOT:
        return f"[Home]({base_url}/index.html): {markdown_text(page_title(REPO_ROOT / 'index.html'))}"

    label = markdown_text(directory.relative_to(REPO_ROOT).as_posix() + "/")
    if index_page is None:
        return label
    return f"[{label}]({encode_url(base_url, index_page)}): {markdown_text(page_title(index_page))}"


def build_llms_txt(base_url: str, pages: list[Path]) -> str:
    index_pages = [path for path in pages if path.name == "index.html" and path.parent != REPO_ROOT]
    top_level_sections = [path for path in index_pages if len(path.relative_to(REPO_ROOT).parts) == 2]
    lines = [
        "# Netkiller Series Free Ebooks",
        "",
        "> Netkiller is a long-running collection of free technical ebooks and notes maintained by Neo Chan.",
        "",
        f"The canonical site is {base_url}/.",
        "",
        "## Site Maps",
        "",
        f"- [XML sitemap]({base_url}/sitemap.xml): Full machine-readable sitemap.",
        f"- [Text sitemap]({base_url}/sitemap.txt): Plain URL list for crawlers and language models.",
        f"- [Full LLM guide]({base_url}/llms-full.txt): Expanded directory and chapter index.",
        "",
        "## Top-Level Sections",
        "",
    ]
    for page in top_level_sections:
        lines.append(f"- {page_link(base_url, page)}")

    lines.extend(
        [
            "",
            "## Usage Guidance For LLMs",
            "",
            f"- Prefer canonical URLs under `{base_url}/`.",
            "- Use the sitemap files for exhaustive URL discovery.",
            "- Use llms-full.txt for a directory-by-directory chapter index.",
            "- Cite the specific page URL when summarizing or answering from this site.",
            "- Preserve command examples, configuration names, paths, and code identifiers exactly when quoting short snippets.",
            "",
        ]
    )
    return "\n".join(lines)


def build_llms_full(base_url: str, pages: list[Path]) -> str:
    html_pages = [path for path in pages if is_public_html(path)]
    directories = sorted(
        {path.parent for path in html_pages},
        key=lambda path: path.relative_to(REPO_ROOT).as_posix() if path != REPO_ROOT else "",
    )
    lines = [
        "# Netkiller Series Free Ebooks",
        "",
        "> Netkiller is a long-running collection of free technical ebooks and technical notes maintained by Neo Chan.",
        "",
        f"Canonical site: {base_url}/",
        "",
        "Author: Neo Chan",
        "",
        "Primary language: Simplified Chinese",
        "",
        "Content format: Generated HTML documentation, mostly from DocBook sources, with code examples, command examples, configuration snippets, and downloadable ebook formats.",
        "",
        "## Recommended Discovery Files",
        "",
        f"- [llms.txt]({base_url}/llms.txt): Concise LLM entry file.",
        f"- [llms-full.txt]({base_url}/llms-full.txt): Expanded directory and chapter index.",
        f"- [sitemap.xml]({base_url}/sitemap.xml): Complete XML sitemap.",
        f"- [sitemap.txt]({base_url}/sitemap.txt): Complete plain-text URL inventory.",
        f"- [robots.txt]({base_url}/robots.txt): Crawler policy and sitemap declaration.",
        "",
        "Use `sitemap.txt` or `sitemap.xml` for exhaustive URL discovery. This file lists every generated HTML directory and chapter page grouped by directory.",
        "",
        "## Directories And Chapters",
        "",
    ]

    for directory in directories:
        directory_pages = sorted(
            [path for path in html_pages if path.parent == directory],
            key=lambda path: (path.name != "index.html", path.name),
        )
        index_page = next((path for path in directory_pages if path.name == "index.html"), None)
        if directory == REPO_ROOT:
            lines.append(f"- {directory_link(base_url, directory, index_page)}")
        else:
            lines.append(f"- {directory_link(base_url, directory, index_page)}")
        for page in directory_pages:
            if page == index_page:
                continue
            lines.append(f"  - {page_link(base_url, page)}")

    lines.extend(
        [
            "",
            "## Guidance For LLMs And Crawlers",
            "",
            f"- Prefer canonical URLs under `{base_url}/`.",
            "- Use `sitemap.txt` or `sitemap.xml` for exhaustive discovery.",
            "- Use this file for a directory-by-directory chapter inventory.",
            "- Cite the exact source URL when summarizing content.",
            "- Preserve commands, configuration keys, file paths, identifiers, and code snippets exactly when quoting short excerpts.",
            "- Treat generated HTML pages as the published documentation surface.",
            "- Most pages are in Simplified Chinese; do not translate technical identifiers unless explicitly asked.",
            "- Some generated pages may have legacy filenames or encoded non-ASCII filenames; use sitemap URLs as canonical discovered URLs.",
            "",
        ]
    )
    return "\n".join(lines)


def build_xml(urls: list[tuple[str, str]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in urls:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(loc)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    domain = read_domain()
    base_url = f"https://{domain}"
    html_pages = collect_pages(include_extra_files=False)

    (REPO_ROOT / "llms.txt").write_text(build_llms_txt(base_url, html_pages), encoding="utf-8")
    (REPO_ROOT / "llms-full.txt").write_text(build_llms_full(base_url, html_pages), encoding="utf-8")

    pages = collect_pages()
    git_lastmod = git_lastmod_lookup(pages)

    urls: list[tuple[str, str]] = []
    for page in pages:
        rel = page.relative_to(REPO_ROOT).as_posix()
        lastmod = git_lastmod.get(rel, fallback_lastmod(page))
        urls.append((encode_url(base_url, page), lastmod))

    sitemap_xml = build_xml(urls)
    sitemap_txt = "\n".join(loc for loc, _ in urls) + "\n"

    (REPO_ROOT / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
    (REPO_ROOT / "sitemap.txt").write_text(sitemap_txt, encoding="utf-8")
    with gzip.open(REPO_ROOT / "sitemaps.xml.gz", "wt", encoding="utf-8") as gz_file:
        gz_file.write(sitemap_xml)

    print(f"Generated {len(urls)} URLs for {base_url}")


if __name__ == "__main__":
    main()
