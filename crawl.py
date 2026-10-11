#!/usr/bin/env python3
"""
Crawler and Markdown exporter for Edward W. Pritchard's stories
Source: https://eddwardwpritchard.blogspot.com/
"""

import os
import sys
import json
import re
import time
import urllib.request
from datetime import datetime

try:
    import html2text
except ImportError:
    print("Error: html2text is required. Run: pip install html2text or .venv/bin/pip install html2text")
    sys.exit(1)


FEED_BASE_URL = "https://eddwardwpritchard.blogspot.com/feeds/posts/default?alt=json"
RAW_POSTS_FILE = "raw_posts.json"


def fetch_all_posts():
    """Fetch all posts from Blogger JSON feed using pagination."""
    total_results = None
    entries = []
    start_index = 1
    max_results = 150

    print("Fetching stories from Blogger feed...")
    while True:
        url = f"{FEED_BASE_URL}&start-index={start_index}&max-results={max_results}"
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (StoryCrawler/1.0)"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        feed = data.get("feed", {})
        if total_results is None:
            total_results = int(feed.get("openSearch$totalResults", {}).get("$t", 0))
            print(f"Total stories available on blog: {total_results}")

        batch = feed.get("entry", [])
        if not batch:
            break

        entries.extend(batch)
        print(f"  Fetched {len(batch)} stories (total: {len(entries)}/{total_results}) in {time.time()-t0:.2f}s")

        if len(entries) >= total_results or len(batch) < max_results:
            break

        start_index += len(batch)
        time.sleep(0.15)

    print(f"Successfully fetched all {len(entries)} stories.")
    with open(RAW_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Saved raw data to {RAW_POSTS_FILE}")
    return entries


def slugify(text, max_len=60):
    """Convert text to URL-safe filename slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    slug = text[:max_len].rstrip("-")
    return slug or "untitled"


def clean_markdown_content(html_content, title):
    """Convert HTML content to clean Markdown with appropriate headings."""
    if not html_content or not html_content.strip():
        return f"# {title}\n\n*(No content)*"

    # Strip published abbr tags injected by Blogger
    clean_html = re.sub(r"<abbr[^>]*class=[\"']published[\"'][^>]*>.*?</abbr>", "", html_content, flags=re.IGNORECASE)

    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    h2t.ignore_links = False
    h2t.ignore_images = False

    md = h2t.handle(clean_html)

    # Remove Blogger administrative widgets, edit icons, and empty links
    md = re.sub(r"\[!\[.*?\]\(https?://[^)]*blogblog\.com/img/icon18_[^)]+\)\]\([^)]+\)", "", md)
    md = re.sub(r"!\[.*?\]\(https?://[^)]*blogblog\.com/img/icon18_[^)]+\)", "", md)
    md = re.sub(r"\[\]\(https?://www\.blogger\.com/null\)", "", md)
    md = re.sub(r"##\s*ADBRIGHT\s*", "", md)

    # Normalize whitespace line-by-line
    raw_lines = [line.strip() for line in md.split("\n")]
    cleaned_lines = []
    for line in raw_lines:
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        else:
            cleaned_lines.append(line)

    # Ensure document starts with # Title without duplicating it if body starts with title
    if cleaned_lines:
        first_clean = re.sub(r"[^\w\s]", "", cleaned_lines[0]).strip().lower()
        t_clean = re.sub(r"[^\w\s]", "", title).strip().lower()
        if first_clean and t_clean and (first_clean == t_clean or first_clean.startswith(t_clean) or t_clean.startswith(first_clean)):
            cleaned_lines[0] = f"# {title}"
        else:
            cleaned_lines.insert(0, f"# {title}")
            cleaned_lines.insert(1, "")
    else:
        cleaned_lines = [f"# {title}"]

    return "\n".join(cleaned_lines).strip()


def resolve_title(entry):
    """Resolve post title, inferring from content or URL slug if blank."""
    title = entry.get("title", {}).get("$t", "").strip()
    if title:
        return title

    # Check URL slug
    url = next((l.get("href") for l in entry.get("link", []) if l.get("rel") == "alternate"), "")
    url_slug = url.split("/")[-1].replace(".html", "")

    content = entry.get("content", {}).get("$t", "")
    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    lines = [line.strip() for line in h2t.handle(content).split("\n") if line.strip()]

    # If first line looks like a title, use it
    if lines:
        first = lines[0]
        # Remove trailing author or fiction tags if present on the same line
        first_clean = re.sub(r"\s+(?:fiction|editorial fiction|part \d+).*$", "", first, flags=re.IGNORECASE).strip()
        if 2 < len(first_clean) < 80:
            return first_clean

    # Fallback to URL slug
    clean_slug = re.sub(r"[-_]+", " ", url_slug)
    clean_slug = re.sub(r"\s+(?:fiction|edward|pritchard).*$", "", clean_slug, flags=re.IGNORECASE).strip()
    return clean_slug.title() if clean_slug else "Untitled Story"


def escape_yaml(text):
    """Safely escape text for single-line YAML string values."""
    if not text:
        return '""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def export_posts(posts):
    """Export all posts to organized markdown files and generate indices."""
    used_paths = set()
    processed_posts = []

    print(f"Processing and writing {len(posts)} stories...")

    for entry in posts:
        post_id = entry.get("id", {}).get("$t", "")
        pub_raw = entry.get("published", {}).get("$t", "")
        updated_raw = entry.get("updated", {}).get("$t", "")
        author_name = entry.get("author", [{}])[0].get("name", {}).get("$t", "Edward W. Pritchard")
        url = next((l.get("href") for l in entry.get("link", []) if l.get("rel") == "alternate"), "")
        categories = [c.get("term", "").strip() for c in entry.get("category", []) if c.get("term")]

        title = resolve_title(entry)
        date_str = pub_raw[:10] if pub_raw else "unknown-date"
        year = date_str[:4] if len(date_str) >= 4 and date_str[:4].isdigit() else "undated"

        url_slug = url.split("/")[-1].replace(".html", "")
        slug = slugify(title)
        if not slug or slug == "untitled":
            slug = slugify(url_slug) or "untitled"

        base_filename = f"{date_str}-{slug}"
        filename = f"{base_filename}.md"
        rel_path = f"{year}/{filename}"

        counter = 1
        while rel_path in used_paths:
            counter += 1
            filename = f"{base_filename}-{counter}.md"
            rel_path = f"{year}/{filename}"

        used_paths.add(rel_path)

        # Build Markdown content with YAML frontmatter
        body_md = clean_markdown_content(entry.get("content", {}).get("$t", ""), title)

        frontmatter = [
            "---",
            f"title: {escape_yaml(title)}",
            f"date: {pub_raw}",
            f"updated: {updated_raw}",
            f"author: {escape_yaml(author_name)}",
            f"url: {escape_yaml(url)}",
            f"post_id: {escape_yaml(post_id)}",
        ]
        if categories:
            frontmatter.append("categories:")
            for cat in categories:
                frontmatter.append(f"  - {escape_yaml(cat)}")
        else:
            frontmatter.append("categories: []")
        frontmatter.append("---\n")

        full_content = "\n".join(frontmatter) + "\n" + body_md + "\n"

        # Ensure directory exists
        os.makedirs(year, exist_ok=True)
        file_path = os.path.join(year, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        processed_posts.append({
            "title": title,
            "published": pub_raw,
            "date": date_str,
            "year": year,
            "rel_path": rel_path,
            "filename": filename,
            "url": url,
            "categories": categories,
        })

    # Sort posts chronologically (oldest to newest)
    processed_posts.sort(key=lambda x: (x["published"], x["title"]))

    print(f"Successfully wrote {len(processed_posts)} story markdown files.")

    # Generate yearly READMEs
    years = sorted(list(set(p["year"] for p in processed_posts)))
    for y in years:
        year_posts = [p for p in processed_posts if p["year"] == y]
        readme_path = os.path.join(y, "README.md")
        lines = [
            f"# Edward W. Pritchard Stories – {y}",
            "",
            f"Total stories in {y}: **{len(year_posts)}**",
            "",
            "| Date | Title | Categories | Original Link |",
            "| --- | --- | --- | --- |",
        ]
        for p in year_posts:
            cats = ", ".join(f"`{c}`" for c in p["categories"]) if p["categories"] else "—"
            clean_t = p["title"].replace("|", "\\|")
            lines.append(f"| {p['date']} | [{clean_t}]({p['filename']}) | {cats} | [Blogspot]({p['url']}) |")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"  Generated {readme_path} ({len(year_posts)} stories)")

    # Generate master INDEX.md
    print("Generating master INDEX.md...")
    index_lines = [
        "# Complete Story Catalog – Edward W. Pritchard",
        "",
        f"This catalog indexes all **{len(processed_posts)}** stories by Edward W. Pritchard, sorted chronologically.",
        "",
        "## Quick Navigation by Year",
        "",
    ]
    year_nav = []
    for y in years:
        y_count = sum(1 for p in processed_posts if p["year"] == y)
        year_nav.append(f"- **[{y}]({y}/README.md)** ({y_count} stories)")
    index_lines.extend(year_nav)
    index_lines.append("")
    index_lines.append("---")
    index_lines.append("")
    index_lines.append("## Chronological List")
    index_lines.append("")
    index_lines.append("| Date | Title | Year Folder | Categories | Original Link |")
    index_lines.append("| --- | --- | --- | --- | --- |")
    for p in processed_posts:
        cats = ", ".join(f"`{c}`" for c in p["categories"]) if p["categories"] else "—"
        clean_t = p["title"].replace("|", "\\|")
        index_lines.append(f"| {p['date']} | [{clean_t}]({p['rel_path']}) | [{p['year']}/]({p['year']}/README.md) | {cats} | [Blogspot]({p['url']}) |")

    with open("INDEX.md", "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")
    print("Generated master INDEX.md")

    # Generate root README.md
    print("Generating root README.md...")
    readme_lines = [
        "# Edward W. Pritchard: Stories Archive",
        "",
        "A complete local Markdown archive of all stories from [Edward W. Pritchard's blog](https://eddwardwpritchard.blogspot.com/).",
        "",
        "> \"These are the short stories of Edward w Pritchard of Akron, Ohio. Stories are updated frequently and on many subjects. These stories are fiction with characters, dates and places sometimes based upon fact or having real life names or characters. But it is always just fiction, story telling.\"",
        "",
        "## Archive Overview",
        "",
        f"- **Total Stories:** {len(processed_posts)}",
        f"- **Date Range:** {processed_posts[0]['date']} to {processed_posts[-1]['date']}",
        f"- **Years Active:** {len(years)} years ({years[0]} – {years[-1]})",
        f"- **Full Catalog:** See [INDEX.md](INDEX.md) for the searchable chronological list.",
        "",
        "## Stories by Year",
        "",
        "| Year | Stories | Year Index |",
        "| --- | --- | --- |",
    ]
    for y in years:
        y_count = sum(1 for p in processed_posts if p["year"] == y)
        readme_lines.append(f"| {y} | {y_count} | [Browse {y} Stories]({y}/README.md) |")

    readme_lines.extend([
        "",
        "## Directory Structure",
        "",
        "Stories are organized into directories by **Year** (`YYYY/`), with each story stored in a standalone Markdown file named `YYYY-MM-DD-<slug>.md`.",
        "",
        "Each story file contains:",
        "- **YAML Frontmatter**: title, published date, author, original URL, post ID, and categories.",
        "- **Clean Markdown Body**: preserving paragraphs, dialogues, images, and formatting.",
        "",
        "```",
        "ed/",
        "├── README.md           # This archive summary",
        "├── INDEX.md            # Complete chronological catalog of all stories",
        "├── crawl.py            # Python crawler to sync or update posts",
        "├── requirements.txt    # Python dependencies",
        "├── raw_posts.json      # Cached JSON responses from Blogger",
        "├── 2010/               # Stories published in 2010 (523 stories)",
        "│   ├── README.md       # Table of contents for 2010",
        "│   └── 2010-01-05-...md",
        "├── ...",
        "└── 2026/               # Stories published in 2026",
        "    ├── README.md",
        "    └── 2026-07-13-...md",
        "```",
        "",
        "## How to Update / Re-run Crawler",
        "",
        "To re-crawl and sync new posts:",
        "```bash",
        "# Set up virtual environment",
        "python3 -m venv .venv",
        "source .venv/bin/activate",
        "pip install -r requirements.txt",
        "",
        "# Run crawler (fetches newly added stories if any)",
        "python crawl.py --fetch",
        "```",
    ])

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines) + "\n")
    print("Generated root README.md")


def main():
    fetch_new = "--fetch" in sys.argv or not os.path.exists(RAW_POSTS_FILE)

    if fetch_new:
        posts = fetch_all_posts()
    else:
        print(f"Loading existing posts from {RAW_POSTS_FILE} (use --fetch to redownload)...")
        with open(RAW_POSTS_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
        print(f"Loaded {len(posts)} posts.")

    export_posts(posts)
    print("\nAll done!")


if __name__ == "__main__":
    main()
