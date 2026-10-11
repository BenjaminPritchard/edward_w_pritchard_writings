#!/usr/bin/env python3
"""
Edward W. Pritchard Stories Archive - Static Site Generator for GitHub Pages
Compiles 2,630+ Markdown stories into a fast, browseable, minimal-HTML static site
with demoscene aesthetics, pinned longform stories, live search, and individual reader pages.
"""

import os
import sys
import glob
import re
import json
import time
import html
from datetime import datetime

try:
    import markdown
except ImportError:
    print("Error: 'markdown' package required. Run: pip install markdown")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.abspath(os.path.dirname(__file__))


def clean_yaml_val(val):
    val = val.strip()
    return val.strip("\"'")


def clean_narrative_text(text, author="Edward W. Pritchard"):
    """Strip recurring bylines, markdown escapes, and artifacts to get clean narrative text."""
    # Strip markdown links and image tags
    t = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", text)
    t = re.sub(r"!\[.*?\]\(.*?\)", "", t)
    t = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", t)
    t = re.sub(r"\\([.!-*])", r"\1", t)

    byline_patterns = [
        r"^fiction\b",
        r"^edward\s+w\.?\s+pritchard\b",
        r"^edward\s+pritchard\b",
        r"^draft\s+\d+\b",
        r"^part\s+\d+\b",
        r"^act\s+\d+\b",
        r"^scene\s+\d+\b",
    ]
    for pat in byline_patterns:
        t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()

    return t.strip()


def parse_story_file(filepath):
    """Parse Markdown file with frontmatter into story dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("---", 2)
    meta = {}
    body = ""
    categories = []

    if len(parts) >= 3:
        fm = parts[1]
        body = parts[2].strip()

        # Parse YAML frontmatter
        in_categories = False
        for line in fm.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("title:"):
                in_categories = False
                meta["title"] = clean_yaml_val(line_str[len("title:"):])
            elif line_str.startswith("date:"):
                in_categories = False
                date_val = clean_yaml_val(line_str[len("date:"):])
                meta["date_raw"] = date_val
                meta["date"] = date_val[:10] if len(date_val) >= 10 else ""
                meta["year"] = date_val[:4] if len(date_val) >= 4 else ""
            elif line_str.startswith("author:"):
                in_categories = False
                meta["author"] = clean_yaml_val(line_str[len("author:"):])
            elif line_str.startswith("url:"):
                in_categories = False
                meta["url"] = clean_yaml_val(line_str[len("url:"):])
            elif line_str.startswith("post_id:"):
                in_categories = False
                meta["post_id"] = clean_yaml_val(line_str[len("post_id:"):])
            elif line_str.startswith("categories:"):
                val = clean_yaml_val(line_str[len("categories:"):])
                if val == "[]" or not val:
                    in_categories = (val == "")
                elif val.startswith("[") and val.endswith("]"):
                    items = val[1:-1].split(",")
                    for it in items:
                        c = clean_yaml_val(it)
                        if c:
                            categories.append(c)
                else:
                    in_categories = True
            elif in_categories and line_str.startswith("-"):
                c = clean_yaml_val(line_str[1:])
                if c:
                    categories.append(c)
            elif not line.startswith(" ") and not line.startswith("\t"):
                in_categories = False
    else:
        body = content

    slug = os.path.splitext(os.path.basename(filepath))[0]
    title = meta.get("title") or slug.replace("-", " ")
    author = meta.get("author") or "Edward W. Pritchard"
    date_str = meta.get("date", "")
    year_str = meta.get("year", date_str[:4] if len(date_str) >= 4 else "Unknown")

    # Word count and read time
    words = len(body.split())
    read_min = max(1, (words + 150) // 200)

    # Clean narrative excerpt
    excerpt_chunks = []
    for line in body.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith("#"):
            continue
        clean_line = clean_narrative_text(line_s, author)
        if clean_line:
            excerpt_chunks.append(clean_line)
        if len(" ".join(excerpt_chunks)) > 260:
            break

    excerpt = " ".join(excerpt_chunks)[:250].strip()
    if len(excerpt) == 250:
        excerpt += "..."
    if not excerpt:
        excerpt = title

    return {
        "id": slug,
        "title": title,
        "author": author,
        "date": date_str,
        "date_raw": meta.get("date_raw", ""),
        "year": year_str,
        "url": meta.get("url", ""),
        "categories": categories,
        "body_md": body,
        "word_count": words,
        "read_minutes": read_min,
        "excerpt": excerpt,
        "filepath": filepath,
        "rel_html_path": f"stories/{year_str}/{slug}.html",
    }


def clean_story_body_for_html(body, title, author):
    """Format body nicely, skipping duplicate titles and styling bylines."""
    lines = body.splitlines()
    cleaned = []
    skip_first_title = True

    for line in lines:
        s = line.strip()
        # Skip duplicate title at the top
        if skip_first_title and (s.startswith("# ") or s.lower() == title.lower()):
            skip_first_title = False
            continue
        skip_first_title = False

        # Clean empty blogger image/link tags
        if re.match(r"^\[!\[.*?\]\(.*?\)\]\(.*?\)$", s) or s == "[](http://www.blogger.com/null)":
            continue

        # Subhead / byline formatting
        if s.lower() in ["fiction", author.lower(), "edward w pritchard", "edward pritchard"]:
            cleaned.append(f'<div class="story-byline-tag">{html.escape(s.upper())}</div>\n')
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def render_html_page(title, body_content, rel_root="../../", extra_head="", is_story=False):
    """Wrap content in site boilerplate."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} - Edward W. Pritchard Archive</title>
  <meta name="description" content="Edward W. Pritchard short stories and writings archive (2010-2026)">
  <link rel="stylesheet" href="{rel_root}css/style.css">
  {extra_head}
</head>
<body data-theme="dark" data-root="{rel_root}">
{body_content}
  <script src="{rel_root}js/stories-data.js" defer></script>
  <script src="{rel_root}js/app.js" defer></script>
</body>
</html>"""


def build_single_story_page(story, prev_story, next_story):
    """Generate static HTML for one individual story."""
    rel_root = "../../"
    clean_md = clean_story_body_for_html(story["body_md"], story["title"], story["author"])
    body_html = markdown.markdown(clean_md, extensions=["extra", "smarty"])

    cats_html = ""
    if story["categories"]:
        cats_html = "".join([f'<span class="tag-badge">#{html.escape(c)}</span>' for c in story["categories"]])

    blogspot_link = ""
    if story["url"]:
        blogspot_link = f'<a href="{story["url"]}" target="_blank" rel="noopener" class="btn-icon">🔗 Original Blogspot</a>'

    prev_card = ""
    if prev_story:
        prev_card = f"""
        <a href="{rel_root}{prev_story['rel_html_path']}" class="nav-story-card">
          <span class="nav-story-dir">&larr; Previous Story</span>
          <span class="nav-story-title">{html.escape(prev_story['title'])}</span>
        </a>"""
    else:
        prev_card = "<div></div>"

    next_card = ""
    if next_story:
        next_card = f"""
        <a href="{rel_root}{next_story['rel_html_path']}" class="nav-story-card" style="text-align: right;">
          <span class="nav-story-dir">Next Story &rarr;</span>
          <span class="nav-story-title">{html.escape(next_story['title'])}</span>
        </a>"""
    else:
        next_card = "<div></div>"

    content = f"""
  <div class="reading-progress-bar"></div>

  <nav class="site-nav">
    <div class="container site-nav-inner">
      <a href="{rel_root}index.html" class="brand-link">
        <span>EDWARD W. PRITCHARD</span>
        <span class="brand-badge">ARCHIVE</span>
      </a>
      <div class="nav-controls">
        <a href="{rel_root}index.html" class="btn-icon">🏠 Archive</a>
        <a href="{rel_root}years/{story['year']}.html" class="btn-icon">📅 {story['year']}</a>
        <button id="random-story-btn" class="btn-icon" title="Random Story (r)">🎲 Random</button>
        <button id="theme-toggle-btn" class="btn-icon" title="Toggle Theme (t)">🌓 Theme</button>
      </div>
    </div>
  </nav>

  <main class="reader-container">
    <header class="story-header">
      <div class="story-breadcrumb">
        <a href="{rel_root}index.html">Archive</a> &rsaquo; 
        <a href="{rel_root}years/{story['year']}.html">{story['year']}</a> &rsaquo; 
        <span>{html.escape(story['title'])}</span>
      </div>

      <h1 class="story-page-title">{html.escape(story['title'])}</h1>

      <div class="story-meta-box">
        <span>📅 {story['date']}</span>
        <span>📖 {story['word_count']:,} words</span>
        <span>⏱️ ~{story['read_minutes']} min read</span>
        <span class="story-author">✍️ {html.escape(story['author'])}</span>
      </div>

      {f'<div class="tag-list">{cats_html}</div>' if cats_html else ''}

      <div class="reader-toolbar">
        <div class="toolbar-group">
          <button id="font-decrease-btn" class="btn-icon" title="Decrease font size">A-</button>
          <button id="font-increase-btn" class="btn-icon" title="Increase font size">A+</button>
        </div>
        <div class="toolbar-group">
          {blogspot_link}
        </div>
      </div>
    </header>

    <article class="story-body">
      {body_html}
    </article>

    <div class="story-end-marker">
      ◈ ◈ ◈ &nbsp; [ END OF STORY ] &nbsp; ◈ ◈ ◈<br>
      <small style="opacity: 0.7; letter-spacing: 0.05em; margin-top: 0.5rem; display: inline-block;">EDWARD W. PRITCHARD ARCHIVES</small>
    </div>

    <nav class="story-nav-footer">
      {prev_card}
      {next_card}
    </nav>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-copy">
        <strong>Edward W. Pritchard Writings Archive</strong> &bull; Stories published 2010&ndash;2026<br>
        Preserved as static HTML for GitHub Pages.
      </div>
      <div class="footer-links">
        <a href="{rel_root}index.html">Archive Home</a>
        <a href="{rel_root}years/{story['year']}.html">{story['year']} Collection</a>
      </div>
    </div>
  </footer>
"""
    return render_html_page(story["title"], content, rel_root=rel_root, is_story=True)


def build_year_page(year, stories_in_year, all_years):
    """Generate static HTML for a year archive."""
    rel_root = "../"
    stories_in_year_sorted = sorted(stories_in_year, key=lambda s: s["date"])

    total_words = sum(s["word_count"] for s in stories_in_year)
    longest_in_year = max(stories_in_year, key=lambda s: s["word_count"])

    year_links = " ".join([
        f'<a href="{rel_root}years/{y}.html" class="year-btn {"active" if y == year else ""}">{y}</a>'
        for y in all_years
    ])

    rows = []
    for s in stories_in_year_sorted:
        cats_str = ", ".join(s["categories"]) if s["categories"] else "—"
        rows.append(f"""
        <article class="story-card">
          <div>
            <div class="card-header-row">
              <span class="card-date">📅 {s['date']}</span>
              <span class="card-words-tag">📖 {s['word_count']:,} w &bull; ~{s['read_minutes']}m</span>
            </div>
            <h3 class="card-title">
              <a href="{rel_root}{s['rel_html_path']}">{html.escape(s['title'])}</a>
            </h3>
            <p class="card-excerpt">{html.escape(s['excerpt'])}</p>
            {f'<div class="tag-list"><span class="tag-badge">{html.escape(cats_str)}</span></div>' if s['categories'] else ''}
          </div>
          <div class="card-footer">
            <div class="card-actions">
              <a href="{rel_root}{s['rel_html_path']}" class="btn-card-read">Read Story &rarr;</a>
            </div>
          </div>
        </article>""")

    content = f"""
  <nav class="site-nav">
    <div class="container site-nav-inner">
      <a href="{rel_root}index.html" class="brand-link">
        <span>EDWARD W. PRITCHARD</span>
        <span class="brand-badge">ARCHIVE</span>
      </a>
      <div class="nav-controls">
        <a href="{rel_root}index.html" class="btn-icon">🏠 Archive Home</a>
        <button id="random-story-btn" class="btn-icon" title="Random Story (r)">🎲 Random</button>
        <button id="theme-toggle-btn" class="btn-icon" title="Toggle Theme (t)">🌓 Theme</button>
      </div>
    </div>
  </nav>

  <header class="hero-banner">
    <div class="container">
      <h1 class="hero-header-title">{year} Story Archive</h1>
      <p class="hero-subtitle">
        Exploring all {len(stories_in_year):,} short stories and writings published by Edward W. Pritchard in {year}.
      </p>

      <div class="stats-bar">
        <div class="stat-pill">
          <span class="stat-label">Stories</span>
          <span class="stat-val">{len(stories_in_year):,}</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Total Words</span>
          <span class="stat-val">{total_words:,}</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Longest Story</span>
          <span class="stat-val">{longest_in_year['word_count']:,} words</span>
        </div>
      </div>

      <div style="margin-top: 1.5rem;" class="year-pills-wrap">
        <a href="{rel_root}index.html" class="year-btn">ALL</a>
        {year_links}
      </div>
    </div>
  </header>

  <main class="container section-catalog">
    <div class="results-status-bar">
      <span>Showing <span class="results-count">{len(stories_in_year):,}</span> stories from {year}</span>
    </div>

    <div class="story-grid">
      {"".join(rows)}
    </div>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-copy">
        <strong>Edward W. Pritchard Writings Archive</strong> &bull; {year} Collection ({len(stories_in_year):,} stories)<br>
        Static archive generated for GitHub Pages.
      </div>
      <div class="footer-links">
        <a href="{rel_root}index.html">Archive Home</a>
      </div>
    </div>
  </footer>
"""
    return render_html_page(f"{year} Stories", content, rel_root=rel_root)


def build_index_page(stories, pinned_stories, all_years):
    """Generate the master home portal with Pinned Stories, Interactive Filter, and Stats."""
    rel_root = ""
    total_stories = len(stories)
    total_words = sum(s["word_count"] for s in stories)
    longest_story = max(stories, key=lambda s: s["word_count"])

    # Pinned Spotlight Story (#1 Longest)
    spotlight = pinned_stories[0]
    spotlight_cats = "".join([f'<span class="tag-badge">#{html.escape(c)}</span>' for c in spotlight["categories"]])

    # Pinned Stack (#2 to #5)
    pinned_stack_cards = []
    for rank, s in enumerate(pinned_stories[1:5], start=2):
        pinned_stack_cards.append(f"""
        <article class="card-pinned-compact">
          <div class="compact-top">
            <span class="rank-badge">#{rank} Longest</span>
            <span class="date-pill">📅 {s['date']}</span>
          </div>
          <h4 class="compact-title">
            <a href="{s['rel_html_path']}">{html.escape(s['title'])}</a>
          </h4>
          <div class="compact-meta">
            <span class="meta-words-badge">📖 {s['word_count']:,} words</span>
            <span class="meta-read-badge">⏱️ ~{s['read_minutes']} min read</span>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
            {html.escape(s['excerpt'])}
          </p>
        </article>""")

    # Pinned Grid (#6 to #11)
    pinned_grid_cards = []
    for rank, s in enumerate(pinned_stories[5:11], start=6):
        pinned_grid_cards.append(f"""
        <article class="story-card" style="border-color: rgba(255, 42, 133, 0.35);">
          <div>
            <div class="card-header-row">
              <span class="rank-badge">#{rank} Longest</span>
              <span class="card-date">📅 {s['date']}</span>
            </div>
            <h3 class="card-title" style="margin-top: 0.4rem;">
              <a href="{s['rel_html_path']}">{html.escape(s['title'])}</a>
            </h3>
            <div style="font-family: var(--font-mono); font-size: 0.78rem; margin-bottom: 0.6rem;">
              <span style="color: var(--accent-yellow); font-weight: 700;">📖 {s['word_count']:,} words</span> &bull; 
              <span style="color: var(--accent-green);">⏱️ ~{s['read_minutes']}m read</span>
            </div>
            <p class="card-excerpt">{html.escape(s['excerpt'])}</p>
          </div>
          <div class="card-footer">
            <div class="card-actions">
              <a href="{s['rel_html_path']}" class="btn-card-read">Read Story &rarr;</a>
              <button class="btn-card-preview" data-id="{s['id']}">⚡ Preview</button>
            </div>
          </div>
        </article>""")

    # Year buttons
    year_btns = []
    year_btns.append('<button class="year-btn active" data-year="ALL">ALL (' + str(total_stories) + ')</button>')
    for y in all_years:
        count = sum(1 for s in stories if s["year"] == y)
        year_btns.append(f'<button class="year-btn" data-year="{y}">{y} ({count})</button>')

    # Initial static pre-rendered cards (top 24 longest stories)
    initial_cards = []
    for s in stories[:24]:
        cats_html = "".join([f'<span class="tag-badge">#{html.escape(c)}</span>' for c in s["categories"][:3]])
        initial_cards.append(f"""
        <article class="story-card">
          <div>
            <div class="card-header-row">
              <span class="card-date">📅 {s['date']}</span>
              <span class="card-words-tag">📖 {s['word_count']:,} w &bull; ~{s['read_minutes']}m</span>
            </div>
            <h3 class="card-title">
              <a href="{s['rel_html_path']}">{html.escape(s['title'])}</a>
            </h3>
            <p class="card-excerpt">{html.escape(s['excerpt'])}</p>
            {f'<div class="tag-list">{cats_html}</div>' if cats_html else ''}
          </div>
          <div class="card-footer">
            <div class="card-actions">
              <a href="{s['rel_html_path']}" class="btn-card-read">Read Story &rarr;</a>
              <button class="btn-card-preview" data-id="{s['id']}">⚡ Preview</button>
            </div>
          </div>
        </article>""")

    content = f"""
  <nav class="site-nav">
    <div class="container site-nav-inner">
      <a href="index.html" class="brand-link">
        <span>EDWARD W. PRITCHARD</span>
        <span class="brand-badge">ARCHIVE</span>
      </a>
      <div class="nav-controls">
        <a href="#catalog-section" class="btn-icon">🔍 Browse Archive</a>
        <a href="#pinned-section" class="btn-icon">📌 Long Stories</a>
        <button id="random-story-btn" class="btn-icon" title="Random Story (r)">🎲 Random</button>
        <button id="theme-toggle-btn" class="btn-icon" title="Toggle Theme (t)">🌓 Theme</button>
      </div>
    </div>
  </nav>

  <header class="hero-banner">
    <div class="container">
      <h1 class="hero-header-title">The Complete Story Archive</h1>
      <p class="hero-subtitle">
        Every story, novella, vignette, and reflection written by <strong>Edward W. Pritchard</strong> from 2010 through 2026.
      </p>

      <div class="stats-bar">
        <div class="stat-pill">
          <span class="stat-label">Total Stories</span>
          <span class="stat-val">{total_stories:,}</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Archive Years</span>
          <span class="stat-val">{len(all_years)} (2010&ndash;2026)</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Total Wordcount</span>
          <span class="stat-val">{total_words:,}</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Longest Novella</span>
          <span class="stat-val">{longest_story['word_count']:,} words</span>
        </div>
      </div>
    </div>
  </header>

  <!-- INTERACTIVE ARCHIVE CATALOG & SEARCH -->
  <section id="catalog-section" class="section-catalog">
    <div class="container">
      <div class="section-title-wrap">
        <div>
          <h2 class="section-title">Browse Archive</h2>
          <p class="section-subtitle">Instant live search, year-by-year filtering, and sorting across all {total_stories:,} writings.</p>
        </div>
      </div>

      <div class="catalog-controls">
        <div class="search-row">
          <div class="search-input-wrap">
            <span class="search-icon">🔍</span>
            <input type="text" id="search-input" class="search-input" placeholder="Search by title, tag, year, or keyword... (Press '/' to focus)" autocomplete="off">
            <button id="search-clear" class="search-clear-btn" title="Clear search">&times;</button>
          </div>
          <select id="sort-select" class="sort-select" title="Sort stories">
            <option value="longest">Sort: Longest First</option>
            <option value="newest">Sort: Newest First</option>
            <option value="oldest">Sort: Oldest First</option>
            <option value="shortest">Sort: Shortest First</option>
          </select>
        </div>

        <div class="year-pills-wrap">
          {"".join(year_btns)}
        </div>
      </div>

      <div class="results-status-bar">
        <span>Showing <span id="results-count" class="results-count">{total_stories:,}</span> <span id="results-desc">stories</span></span>
        <span style="color: var(--text-dim);">Shortcuts: '/' Search &bull; 'r' Random &bull; 't' Theme</span>
      </div>

      <!-- Dynamic / Pre-rendered Story Grid -->
      <div id="story-grid" class="story-grid">
        {"".join(initial_cards)}
      </div>

      <div id="load-more-wrap" class="load-more-wrap" style="display: none;">
        <button id="load-more-btn" class="btn-load-more">Load More Stories &darr;</button>
      </div>
    </div>
  </section>

  <!-- PINNED SECTION: FEATURED LONGER STORIES / NOVELLAS -->
  <section id="pinned-section" class="section-pinned">
    <div class="container">
      <div class="section-title-wrap">
        <div>
          <h2 class="section-title">
            <span>Pinned Longform Stories</span>
            <span class="badge-neon">Magnum Opuses</span>
          </h2>
          <p class="section-subtitle">
            The longest and most expansive narrative works in the archive (2,000 to 4,400+ words).
          </p>
        </div>
      </div>

      <div class="pinned-layout">
        <!-- Spotlight #1 Longest Story -->
        <article class="card-spotlight">
          <div>
            <div class="spotlight-top">
              <span class="rank-badge">🏆 #1 Longest Novella</span>
              <span class="date-pill">📅 {spotlight['date']}</span>
            </div>
            <h3 class="spotlight-title">
              <a href="{spotlight['rel_html_path']}">{html.escape(spotlight['title'])}</a>
            </h3>
            <div class="meta-stats-row">
              <span class="meta-words-badge">📖 {spotlight['word_count']:,} words</span>
              <span>&bull;</span>
              <span class="meta-read-badge">⏱️ ~{spotlight['read_minutes']} min read</span>
              <span>&bull;</span>
              <span>✍️ {html.escape(spotlight['author'])}</span>
            </div>
            <p class="spotlight-excerpt">{html.escape(spotlight['excerpt'])}</p>
            {f'<div class="tag-list" style="margin-bottom: 1.5rem;">{spotlight_cats}</div>' if spotlight_cats else ''}
          </div>
          <div class="pinned-actions">
            <a href="{spotlight['rel_html_path']}" class="btn-primary">Read Novella &rarr;</a>
            <button class="btn-secondary" onclick="EWP.openModal(window.STORY_ARCHIVE.find(s=>s.id==='{spotlight['id']}'))">⚡ Quick Preview</button>
            {f'<a href="{spotlight["url"]}" target="_blank" rel="noopener" class="btn-secondary">🔗 Blogspot</a>' if spotlight['url'] else ''}
          </div>
        </article>

        <!-- Pinned Stack #2 to #5 -->
        <div class="pinned-stack">
          {"".join(pinned_stack_cards)}
        </div>
      </div>

      <!-- More Longform Works (#6 to #11) -->
      <div style="margin-top: 1.5rem;">
        <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-mono);">
          More Featured Epics (2,200+ Words)
        </h3>
        <div class="story-grid">
          {"".join(pinned_grid_cards)}
        </div>
      </div>
    </div>
  </section>

  <!-- QUICK VIEW MODAL / DRAWER -->
  <div id="quick-modal" class="modal-overlay">
    <div class="modal-content">
      <div class="modal-header">
        <div>
          <h3 id="modal-title" class="modal-title">Story Title</h3>
          <div id="modal-meta" class="modal-meta">Meta details</div>
        </div>
        <button id="modal-close-btn" class="modal-close-btn" title="Close (Esc)">&times;</button>
      </div>
      <div id="modal-body" class="modal-body">
        Story preview content...
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" onclick="EWP.closeModal()">Close</button>
        <a id="modal-full-link" href="#" class="btn-primary">Read Full Story &rarr;</a>
      </div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-copy">
        <strong>Edward W. Pritchard Writings Archive</strong> &bull; 2,631+ Stories (2010&ndash;2026)<br>
        Crafted with minimal HTML &amp; demoscene styling for GitHub Pages.
      </div>
      <div class="footer-links">
        <a href="#catalog-section">Browse Archive</a>
        <a href="#pinned-section">Pinned Stories</a>
        <a href="https://eddwardwpritchard.blogspot.com/" target="_blank" rel="noopener">Original Blog</a>
      </div>
    </div>
  </footer>
"""
    return render_html_page("Complete Archive", content, rel_root=rel_root)


def main():
    t0 = time.time()
    print("=== Building Edward W. Pritchard GitHub Pages Static Archive ===")

    # 1. Discover all story files
    pattern = os.path.join(REPO_ROOT, "20*", "*.md")
    all_files = sorted([f for f in glob.glob(pattern) if not f.endswith("README.md")])
    print(f"Found {len(all_files)} Markdown story files in {REPO_ROOT}")

    if not all_files:
        print("Error: No markdown files found!")
        sys.exit(1)

    # 2. Parse all stories
    print("Parsing stories and calculating metadata...")
    stories = []
    for fp in all_files:
        s = parse_story_file(fp)
        stories.append(s)

    # Sort chronologically ascending
    stories.sort(key=lambda s: (s["date"], s["title"]))

    # Link prev/next pointers
    for i, s in enumerate(stories):
        s["prev"] = stories[i - 1] if i > 0 else None
        s["next"] = stories[i + 1] if i < len(stories) - 1 else None

    # Discover years
    all_years = sorted(list(set(s["year"] for s in stories if s["year"].isdigit())))
    print(f"Archive covers {len(all_years)} years: {all_years[0]} to {all_years[-1]}")

    # Identify longest stories for pinning
    stories_by_length = sorted(stories, key=lambda s: s["word_count"], reverse=True)
    pinned_stories = stories_by_length[:16]
    print("Top pinned stories identified:")
    for rank, ps in enumerate(pinned_stories[:5], start=1):
        print(f"  #{rank}: {ps['word_count']:,} words | {ps['date']} | {ps['title']}")

    # 3. Create output directory tree
    os.makedirs(os.path.join(OUT_DIR, "css"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "js"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "years"), exist_ok=True)
    for y in all_years:
        os.makedirs(os.path.join(OUT_DIR, "stories", y), exist_ok=True)

    # 4. Generate individual story pages
    print(f"Generating {len(stories):,} individual story HTML pages...")
    for s in stories:
        out_html_path = os.path.join(OUT_DIR, s["rel_html_path"])
        html_content = build_single_story_page(s, s["prev"], s["next"])
        with open(out_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    # 5. Generate year archive pages
    print(f"Generating {len(all_years)} year archive pages...")
    for y in all_years:
        stories_in_year = [s for s in stories if s["year"] == y]
        year_html = build_year_page(y, stories_in_year, all_years)
        year_path = os.path.join(OUT_DIR, "years", f"{y}.html")
        with open(year_path, "w", encoding="utf-8") as f:
            f.write(year_html)

    # 6. Generate stories.json and js/stories-data.js for instant client-side search
    print("Generating search index data (stories.json & js/stories-data.js)...")
    search_data = []
    for s in stories_by_length:
        search_data.append({
            "id": s["id"],
            "t": s["title"],
            "d": s["date"],
            "y": s["year"],
            "w": s["word_count"],
            "m": s["read_minutes"],
            "c": s["categories"],
            "e": s["excerpt"],
            "u": s["rel_html_path"],
            "b": s["url"],
        })

    json_str = json.dumps(search_data, separators=(",", ":"), ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "stories.json"), "w", encoding="utf-8") as f:
        f.write(json_str)

    with open(os.path.join(OUT_DIR, "js", "stories-data.js"), "w", encoding="utf-8") as f:
        f.write(f"window.STORY_ARCHIVE = {json_str};\n")

    # 7. Generate master index.html
    print("Generating master index.html portal...")
    index_html = build_index_page(stories_by_length, pinned_stories, all_years)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # 8. GitHub Pages .nojekyll marker
    with open(os.path.join(OUT_DIR, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    elapsed = time.time() - t0
    print(f"=== Build Completed in {elapsed:.2f} seconds! ===")
    print(f"Output Directory: {OUT_DIR}")
    print(f"Total Stories Processed: {len(stories):,}")
    print("To preview locally:")
    print(f"  cd {OUT_DIR} && python3 -m http.server 8080")


if __name__ == "__main__":
    main()
