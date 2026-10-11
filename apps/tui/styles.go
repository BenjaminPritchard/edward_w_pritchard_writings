package main

import (
	"github.com/charmbracelet/lipgloss"
)

// Demoscene / Cyberpunk Palette
var (
	// Base Colors
	colorBgDark     = lipgloss.Color("#0d1117") // Deep obsidian dark
	colorBgCard     = lipgloss.Color("#161b22") // Surface dark
	colorBgSelected = lipgloss.Color("#21262d") // Row selection bg
	colorBorder     = lipgloss.Color("#30363d") // Subtle border

	// Neon / Demoscene Accents
	colorCyan    = lipgloss.Color("#00f0ff") // Electric cyan
	colorMagenta = lipgloss.Color("#ff2a85") // Neon hot pink / magenta
	colorPurple  = lipgloss.Color("#a855f7") // Vivid purple
	colorYellow  = lipgloss.Color("#ffd700") // Neon amber / gold
	colorGreen   = lipgloss.Color("#00ff9d") // Terminal matrix green
	colorBlue    = lipgloss.Color("#38bdf8") // Sky blue

	// Text Colors
	colorTextBright = lipgloss.Color("#f0f6fc")
	colorTextMuted  = lipgloss.Color("#8b949e")
	colorTextDim    = lipgloss.Color("#484f58")

	// Styles
	styleHeaderBanner = lipgloss.NewStyle().
				Foreground(colorCyan).
				Bold(true)

	styleHeaderSub = lipgloss.NewStyle().
			Foreground(colorMagenta).
			Bold(true)

	styleHeaderMeta = lipgloss.NewStyle().
			Foreground(colorTextMuted)

	stylePanelActive = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(colorCyan).
				Padding(0, 1)

	stylePanelInactive = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(colorBorder).
				Padding(0, 1)

	styleListSelected = lipgloss.NewStyle().
				Bold(true).
				Foreground(colorCyan).
				Background(lipgloss.Color("#1f2937"))

	styleListNormal = lipgloss.NewStyle().
			Foreground(colorTextBright)

	styleDate = lipgloss.NewStyle().
			Foreground(colorYellow)

	styleCategoryPill = lipgloss.NewStyle().
				Foreground(colorPurple).
				Background(lipgloss.Color("#271d3d")).
				Padding(0, 1)

	styleYearActive = lipgloss.NewStyle().
			Foreground(colorMagenta).
			Background(lipgloss.Color("#361329")).
			Bold(true).
			Padding(0, 1)

	styleYearInactive = lipgloss.NewStyle().
				Foreground(colorTextMuted).
				Padding(0, 1)

	styleStatusKey = lipgloss.NewStyle().
			Foreground(colorCyan).
			Bold(true)

	styleStatusDesc = lipgloss.NewStyle().
			Foreground(colorTextMuted)

	styleStatusBar = lipgloss.NewStyle().
			Background(colorBgCard).
			Foreground(colorTextBright).
			Padding(0, 1)

	styleReaderTitle = lipgloss.NewStyle().
				Foreground(colorMagenta).
				Bold(true).
				MarginBottom(0)

	styleReaderMeta = lipgloss.NewStyle().
			Foreground(colorBlue)

	styleReaderDivider = lipgloss.NewStyle().
				Foreground(colorBorder)

	styleModal = lipgloss.NewStyle().
			Border(lipgloss.DoubleBorder()).
			BorderForeground(colorMagenta).
			Background(colorBgCard).
			Padding(1, 2)

	styleSearchPrompt = lipgloss.NewStyle().
				Foreground(colorGreen).
				Bold(true)
)

const demosceneLogo = `  ▓█████ ▓█████▄   ▄▄▄█████▓ █    ██  ██▓
  ▓█   ▀ ▒██▀ ██▌  ▓  ██▒ ▓▒ ██  ▓██▒▓██▒
  ▒███   ░██   █▌  ▒ ▓██░ ▒░▓██  ▒██░▒██▒
  ▒▓█  ▄ ░▓█▄   ▌  ░ ▓██▓ ░ ▓▓█  ░██░░██░
  ░▒████▒░▒████▓     ▒██▒ ░ ▒▒█████▓ ░██░
  ░░ ▒░ ░ ▒▒▓  ▒     ▒ ░░   ░▒▓▒ ▒ ▒ ░▓  
   ░ ░  ░ ░ ▒  ▒       ░    ░░▒░ ░ ░  ▒ ░
     ░    ░ ░  ░     ░       ░░░ ░ ░  ▒ ░
     ░  ░   ░                  ░      ░  `
