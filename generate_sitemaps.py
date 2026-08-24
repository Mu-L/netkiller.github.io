#!/usr/bin/env python3
import os
import gzip
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import re

BASE_URL = "https://www.netkiller.cn"
OUTPUT_DIR = Path(".")

def get_html_files():
    """Recursively find all HTML files."""
    html_files = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith('.html'):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(OUTPUT_DIR)
                html_files.append(rel_path)
    return sorted(html_files)

def get_lastmod(filepath):
    """Get last modification date of a file."""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

def url_encode_path(path):
    """URL encode a file path."""
    parts = str(path).split('/')
    encoded_parts = [quote(part, safe='') for part in parts]
    return '/'.join(encoded_parts)

def extract_title(filepath):
    """Extract title from HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(5000)  # Read first 5KB
            match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Clean up title
                title = re.sub(r'\s+', ' ', title)
                return title[:200]  # Limit length
    except:
        pass
    return None

def generate_sitemap_xml(html_files):
    """Generate sitemap.xml."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for rel_path in html_files:
        full_path = OUTPUT_DIR / rel_path
        lastmod = get_lastmod(full_path)
        url_path = url_encode_path(rel_path)
        
        lines.append('  <url>')
        lines.append(f'    <loc>{BASE_URL}/{url_path}</loc>')
        lines.append(f'    <lastmod>{lastmod}</lastmod>')
        lines.append('  </url>')
    
    lines.append('</urlset>')
    
    with open(OUTPUT_DIR / 'sitemap.xml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Generated sitemap.xml with {len(html_files)} URLs")

def generate_sitemap_txt(html_files):
    """Generate sitemap.txt."""
    urls = []
    for rel_path in html_files:
        url_path = url_encode_path(rel_path)
        urls.append(f'{BASE_URL}/{url_path}')
    
    with open(OUTPUT_DIR / 'sitemap.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(urls))
    
    print(f"Generated sitemap.txt with {len(urls)} URLs")

def generate_sitemaps_xml_gz(html_files):
    """Generate sitemaps.xml.gz (compressed version)."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for rel_path in html_files:
        full_path = OUTPUT_DIR / rel_path
        lastmod = get_lastmod(full_path)
        url_path = url_encode_path(rel_path)
        
        lines.append('  <url>')
        lines.append(f'    <loc>{BASE_URL}/{url_path}</loc>')
        lines.append(f'    <lastmod>{lastmod}</lastmod>')
        lines.append('  </url>')
    
    lines.append('</urlset>')
    
    with gzip.open(OUTPUT_DIR / 'sitemaps.xml.gz', 'wt', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Generated sitemaps.xml.gz")

def generate_llms_txt(html_files):
    """Generate llms.txt with directory grouping and titles."""
    lines = []
    lines.append("# Netkiller Series Free Ebooks")
    lines.append("")
    lines.append("> Netkiller is a long-running collection of free technical ebooks and technical notes maintained by Neo Chan.")
    lines.append("")
    lines.append(f"Canonical site: {BASE_URL}/")
    lines.append("")
    lines.append("Author: Neo Chan")
    lines.append("")
    lines.append("Primary language: Simplified Chinese")
    lines.append("")
    lines.append("Content format: Generated HTML documentation, mostly from DocBook sources, with code examples, command examples, configuration snippets, and downloadable ebook formats.")
    lines.append("")
    lines.append("## Recommended Discovery Files")
    lines.append("")
    lines.append(f"- [llms.txt]({BASE_URL}/llms.txt): Complete directory and chapter index for language models.")
    lines.append(f"- [sitemap.xml]({BASE_URL}/sitemap.xml): Complete XML sitemap.")
    lines.append(f"- [sitemap.txt]({BASE_URL}/sitemap.txt): Complete plain-text URL inventory.")
    lines.append(f"- [robots.txt]({BASE_URL}/robots.txt): Crawler policy and sitemap declaration.")
    lines.append("")
    lines.append("Use `sitemap.txt` or `sitemap.xml` for exhaustive URL discovery. This file lists every generated HTML directory and chapter page grouped by directory.")
    lines.append("")
    lines.append("## Directories And Chapters")
    lines.append("")
    
    # Group files by directory
    dirs = {}
    for rel_path in html_files:
        parent = str(rel_path.parent)
        if parent == '.':
            parent = ''
        if parent not in dirs:
            dirs[parent] = []
        dirs[parent].append(rel_path)
    
    # Sort directories
    sorted_dirs = sorted(dirs.keys())
    
    for dir_name in sorted_dirs:
        files = dirs[dir_name]
        
        # Find index.html for directory title
        index_title = None
        for f in files:
            if f.name == 'index.html':
                index_title = extract_title(OUTPUT_DIR / f)
                break
        
        if dir_name:
            dir_display = f"{dir_name}/"
            if index_title:
                lines.append(f"- [{dir_display}]({BASE_URL}/{url_encode_path(Path(dir_name))}/index.html): {index_title}")
            else:
                lines.append(f"- [{dir_display}]({BASE_URL}/{url_encode_path(Path(dir_name))}/index.html): {dir_name}")
        else:
            lines.append(f"- [Home]({BASE_URL}/index.html): Netkiller ebook - Linux ebook")
        
        # List files in directory (excluding index.html)
        for f in sorted(files):
            if f.name != 'index.html':
                title = extract_title(OUTPUT_DIR / f)
                file_display = str(f.relative_to(dir_name)) if dir_name else f.name
                url_path = url_encode_path(f)
                if title:
                    lines.append(f"  - [{file_display}]({BASE_URL}/{url_path}): {title}")
                else:
                    lines.append(f"  - [{file_display}]({BASE_URL}/{url_path}): {f.stem}")
    
    with open(OUTPUT_DIR / 'llms.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Generated llms.txt with {len(html_files)} files in {len(dirs)} directories")

def main():
    print("Scanning HTML files...")
    html_files = get_html_files()
    print(f"Found {len(html_files)} HTML files")
    
    print("\nGenerating sitemaps...")
    generate_sitemap_xml(html_files)
    generate_sitemap_txt(html_files)
    generate_sitemaps_xml_gz(html_files)
    
    print("\nGenerating llms.txt...")
    generate_llms_txt(html_files)
    
    print("\nDone!")

if __name__ == '__main__':
    main()
