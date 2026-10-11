# Edward W. Pritchard Stories Archive &ndash; GitHub Pages (`gh-pages`)

A creative, fast, minimal-HTML static site archiving all **2,633 short stories and essays** written by **Edward W. Pritchard** (2010–2026).

Designed specifically for deployment on **GitHub Pages**, with demoscene-inspired styling, pinned longform stories, instant client-side search, and comfortable reading modes.

---

## Highlights & Features

- **Self-Contained Minimal HTML**:
  - Zero heavy frontend frameworks or external runtime dependencies.
  - Generates standalone, semantic HTML5 pages for every individual story and year collection.
  - Zero CORS dependencies: works equally well via HTTP or opened directly from disk (`file:///`).
- **Demoscene / Editorial Aesthetic**:
  - Obsidian dark palette (`#0d1117`) with vibrant electric cyan (`#00f0ff`), hot pink/magenta (`#ff2a85`), and neon gold accents.
  - ASCII art header banner adapted from the terminal TUI.
  - Multi-theme support:
    - 🌑 **Dark Obsidian** (Default &ndash; high contrast terminal aesthetic)
    - 📜 **Warm Sepia / Paper** (Warm palette optimized for prolonged novel reading)
    - ☀️ **Crisp Light** (Daylight clean mode)
- **Pinned Longform Showcase**:
  - The front page pins the archive's longest narrative works and novellas (2,000 to 4,400+ words).
  - Prominent spotlight card for `#1 Longest Novella: The man in the Iron Helmet` (4,434 words, ~22 min read), accompanied by ranked cards for the top epics.
- **Interactive Archive Explorer**:
  - **Instant Search**: Real-time filtering across titles, dates, word counts, and tags.
  - **Year Filter Pills**: Instant switching across 17 years (`2010` to `2026`) with live post counts.
  - **Sorting**: Longest First, Newest First, Oldest First, and Shortest First.
  - **Performance Optimization**: Employs CSS `content-visibility: auto; contain-intrinsic-size: auto 140px;` so scrolling through 2,633 cards operates at 60fps.
  - **Quick Preview Modal**: Read excerpts and previews on the fly without losing scroll position.
  - **🎲 Random Story (Dice Roll)**: Instant jump to an unexpected story across the 17-year catalog.
- **Dedicated Reader Experience**:
  - Fluid reading progress bar at the top of the viewport.
  - Adjustable reading font size (`A-` / `A+`).
  - Chapter dividers, demoscene end marker, and previous/next story navigation.
  - Direct links back to the original Blogspot post.

---

## Directory Structure

```text
apps/gh-pages/
├── index.html                   # Main portal (Hero banner, Pinned novellas, Live catalog, Quick reader)
├── stories.json                 # Search index metadata
├── .nojekyll                    # GitHub Pages Jekyll bypass marker
├── build.py                     # Python static site generator (~2.7s for 2,633 stories)
├── Makefile                     # Build and serve targets
├── css/
│   └── style.css                # Responsive stylesheet with themes and animations
├── js/
│   ├── app.js                   # Client interactivity (search, filter, themes, modal, randomizer)
│   └── stories-data.js          # Preloaded data store for zero-CORS file:// compatibility
├── years/                       # Dedicated static year archives (2010.html ... 2026.html)
│   ├── 2010.html
│   └── ...
└── stories/                     # Individual story pages (organized by year)
    ├── 2010/
    │   ├── 2010-03-07-the-man-in-the-iron-helmet.html
    │   └── ...
    └── ...
```

---

## Local Development & Preview

### 1. Preview Locally

From `apps/gh-pages/`:

```bash
make serve
# Or directly:
python3 -m http.server 8080
```

Open `http://localhost:8080` in your web browser.

### 2. Rebuild Static Pages

If new stories are added or scraped:

```bash
make build
# Or directly:
python3 build.py
```

Compiles all 2,633 stories and generates all HTML pages in ~2.7 seconds.

---

## GitHub Pages Deployment
 
To commit the static site directly into a clean, local `gh-pages` branch without switching branches or altering your working tree:
 
```bash
# From apps/gh-pages/:
make deploy
# Or run the script directly:
./deploy.sh

# To commit and immediately push to GitHub:
make push
# Or:
./deploy.sh --push
```
 
You can also run it from the root repository directory:
```bash
./deploy-gh-pages.sh
```
 
### GitHub Repository Configuration
1. Go to your repository on GitHub: **Settings** &rarr; **Pages**.
2. Under **Build and deployment** &gt; **Source**, select **Deploy from a branch**.
3. Under **Branch**, select `gh-pages` and `/ (root)`.
4. Click **Save**. GitHub Pages will deploy your site at `https://<username>.github.io/<repo>/`.
