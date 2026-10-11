# Changelog

All notable changes to the Edward W. Pritchard Writings archive repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Built static HTML web archive (`apps/gh-pages`) prepared for GitHub Pages hosting, compiling all 2,633 stories into minimal HTML with demoscene cyberpunk styling, pinned longform novellas on the homepage, instant client-side search, year filters, theme switcher (Dark, Sepia, Light), reading progress indicator, and modal quick reader.
- Created `apps/gh-pages/deploy.sh` and root runner `deploy-gh-pages.sh` to package and commit the static archive straight into a clean local `gh-pages` branch using isolated git plumbing (`git commit-tree` and temporary index), bypassing working tree checkouts and allowing seamless deployment to GitHub Pages. Added `make deploy` and `make push` Makefile targets.
- Repository-wide and recursive `.gitignore` files ignoring Go binaries (`ed-tui`, `ed-tui-linux-amd64`), Python virtual environments (`.venv/`), bytecode caches (`__pycache__/`), OS metadata (`.DS_Store`), the entire experimental `apps/quality/` directory, and Go embed sync content (`apps/tui/content/`).
- Added multi-platform cross-compilation release target (`make release`) in `apps/tui/Makefile`, compiling standalone zero-dependency binaries for macOS (ARM64 & x86_64), Linux (x86_64 & ARM64), and Windows (x86_64) into `apps/tui/dist/` with auto-generated SHA-256 checksums (`checksums.txt`).
- Initialized local repository `changelog.md` and configured `.agent-notes.md` gitignore rules.
- Standalone Bubbletea/Lipgloss terminal reader TUI (`apps/tui`) with embedded story archive, split-pane layout, full-text search, and year carousel.
- Automated web crawler (`crawl.py`) and cached Blogger JSON feed (`raw_posts.json`).
- Complete Markdown archive of 2,631+ short stories categorized across 17 years (2010–2026) with frontmatter metadata and year-by-year indexes.

### Changed
- Updated root `README.md` with comprehensive documentation for the `ed-tui` terminal reader, live public SSH server access (`ssh benjaminpritchard.org -p 4444` via Charmbracelet Wish), architecture explanation, keyboard shortcuts, and updated repository structure diagram.
- Redesigned homepage layout in `apps/gh-pages`: removed the ASCII art banner and secondary boilerplate subtitle, reordered the main page so "Browse Archive" (live search, filter pills, story cards) appears directly above the pinned longform section, enforced default dark theme with CSS `color-scheme: dark`, and updated navigation controls.

### Fixed
- Fixed Random Story button (`#random-story-btn`) failing to trigger from non-home screens. Extended `render_html_page` in `build.py` to load `stories-data.js` via `defer` across all story and year pages, tagged `<body>` with explicit `data-root` relative paths, enhanced `app.js` with an async fallback archive loader, prevented rolling the currently viewed story, and activated global keyboard shortcuts (`r` for Random, `t` for Theme, `/` for Search).
