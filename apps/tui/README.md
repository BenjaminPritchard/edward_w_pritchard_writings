# Edward W. Pritchard Story Archive – TUI

A demoscene-inspired terminal browser for browsing all 2,633 short stories by Edward W. Pritchard (2010–2026).

Compiled into a **single standalone binary** with all stories embedded via Go `embed.FS`.

```
  ▓█████ ▓█████▄   ▄▄▄█████▓ █    ██  ██▓
  ▓█   ▀ ▒██▀ ██▌  ▓  ██▒ ▓▒ ██  ▓██▒▓██▒
  ▒███   ░██   █▌  ▒ ▓██░ ▒░▓██  ▒██░▒██▒
  ▒▓█  ▄ ░▓█▄   ▌  ░ ▓██▓ ░ ▓▓█  ░██░░██░
  ░▒████▒░▒████▓     ▒██▒ ░ ▒▒█████▓ ░██░
```

## Features

- **Self-Contained**: All 2,633 stories embedded directly into the Go executable. Zero external runtime dependencies.
- **Demoscene Aesthetic**: Dark void background (`#0d1117`), electric cyan, hot magenta, neon amber, and glowing borders.
- **Split-Pane Layout**: Responsive side-by-side view with story list on the left and reader on the right (collapses to single-pane on smaller terminals).
- **Year Carousel & Picker**: Quick-cycle years with `[` and `]` or open the Year Picker modal with `y`.
- **Live Search**: Instant substring search across titles, categories, and full text with `/`.
- **Demoscene Dice Roll**: Jump to a random story anytime with `r`.
- **Chrono & Reverse Sort**: Toggle between chronological and reverse chronological order with `s`.
- **Open in Browser**: Open the original Blogspot post in your default browser with `o`.

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `↑` / `↓` or `k` / `j` | Navigate list / scroll reader |
| `Tab` / `Shift+Tab` | Switch between Story List and Reader pane |
| `Enter` / `l` | Focus Reader / select item |
| `h` | Return focus to Story List |
| `[` / `]` or `←` / `→` | Cycle years (ALL, 2010..2026) |
| `y` | Open Year Picker menu |
| `/` | Live search filter |
| `Esc` | Clear search / close modal |
| `r` | 🎲 Random story |
| `s` | Toggle sort order (Chrono vs Newest) |
| `o` | Open story in web browser |
| `PageUp` / `PageDown` | Fast scroll |
| `g` / `G` | Jump to top / bottom |
| `?` | Help overlay |
| `q` / `Ctrl+C` | Quit |

## Quick Start

```bash
# Run directly from repo root:
./ed

# Or from apps/tui:
./ed-tui

# Build from source:
cd apps/tui
make build
./ed-tui

# Build standalone static binary for Linux server (x86_64):
make build-linux

# Build all cross-platform release binaries + SHA-256 checksums (into dist/):
make release
```

## Public SSH Server

The TUI is hosted live over SSH on port **4444** with no password or keys required:

```bash
ssh -p 4444 benjaminpritchard.org
```

