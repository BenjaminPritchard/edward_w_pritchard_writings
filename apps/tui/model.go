package main

import (
	"fmt"
	"math/rand"
	"os/exec"
	"runtime"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type panel int

const (
	panelList panel = iota
	panelReader
)

type overlay int

const (
	overlayNone overlay = iota
	overlayYearPicker
	overlayHelp
)

type Model struct {
	allStories      []Story
	filteredStories []Story

	years           []string
	yearCounts      map[string]int
	selectedYearIdx int // index in years slice

	cursor     int // index in filteredStories
	listOffset int // scroll offset in story list

	activePanel panel
	activeOverlay overlay

	yearPickerCursor int

	sortNewestFirst bool
	statusMsg       string

	// UI components
	searchInput textinput.Model
	viewport    viewport.Model

	width  int
	height int
	ready  bool
}

func initialModel(stories []Story) Model {
	// Discover all distinct years
	yearSet := make(map[string]int)
	for _, s := range stories {
		if s.Year != "" {
			yearSet[s.Year]++
		}
	}

	var yearsList []string
	yearsList = append(yearsList, "ALL")

	// Order years chronologically
	for y := 2010; y <= 2030; y++ {
		ys := fmt.Sprintf("%d", y)
		if count, ok := yearSet[ys]; ok && count > 0 {
			yearsList = append(yearsList, ys)
		}
	}

	ti := textinput.New()
	ti.Placeholder = "type to filter stories..."
	ti.Prompt = "🔍 "
	ti.PromptStyle = styleSearchPrompt
	ti.CharLimit = 64
	ti.Width = 30

	m := Model{
		allStories:       stories,
		filteredStories:  stories,
		years:            yearsList,
		yearCounts:       yearSet,
		selectedYearIdx:  0,
		cursor:           0,
		listOffset:       0,
		activePanel:      panelList,
		activeOverlay:    overlayNone,
		yearPickerCursor: 0,
		sortNewestFirst:  false,
		searchInput:      ti,
	}

	return m
}

func (m Model) Init() tea.Cmd {
	return nil
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var (
		cmd  tea.Cmd
		cmds []tea.Cmd
	)

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height

		contentHeight := m.height - 6
		if contentHeight < 5 {
			contentHeight = 5
		}

		readerWidth := m.readerWidth()
		if !m.ready {
			m.viewport = viewport.New(readerWidth-4, contentHeight-2)
			m.viewport.Style = lipgloss.NewStyle().Padding(0, 1)
			m.ready = true
		} else {
			m.viewport.Width = readerWidth - 4
			m.viewport.Height = contentHeight - 2
		}
		m.updateReaderContent()

	case tea.KeyMsg:
		// When searching input is focused
		if m.searchInput.Focused() {
			switch msg.String() {
			case "esc", "enter":
				m.searchInput.Blur()
				return m, nil
			default:
				m.searchInput, cmd = m.searchInput.Update(msg)
				m.applyFilter()
				return m, cmd
			}
		}

		// When Year Picker modal is open
		if m.activeOverlay == overlayYearPicker {
			switch msg.String() {
			case "esc", "q", "y":
				m.activeOverlay = overlayNone
				return m, nil
			case "up", "k":
				if m.yearPickerCursor > 0 {
					m.yearPickerCursor--
				}
				return m, nil
			case "down", "j":
				if m.yearPickerCursor < len(m.years)-1 {
					m.yearPickerCursor++
				}
				return m, nil
			case "enter":
				m.selectedYearIdx = m.yearPickerCursor
				m.activeOverlay = overlayNone
				m.applyFilter()
				return m, nil
			}
			return m, nil
		}

		// When Help modal is open
		if m.activeOverlay == overlayHelp {
			switch msg.String() {
			case "esc", "q", "?", "enter":
				m.activeOverlay = overlayNone
				return m, nil
			}
			return m, nil
		}

		// Global Hotkeys
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit

		case "?":
			m.activeOverlay = overlayHelp
			return m, nil

		case "y":
			m.activeOverlay = overlayYearPicker
			m.yearPickerCursor = m.selectedYearIdx
			return m, nil

		case "[", "left":
			// Cycle to previous year
			if m.activePanel == panelList {
				if m.selectedYearIdx > 0 {
					m.selectedYearIdx--
				} else {
					m.selectedYearIdx = len(m.years) - 1
				}
				m.applyFilter()
				return m, nil
			}

		case "]", "right":
			// Cycle to next year
			if m.activePanel == panelList {
				if m.selectedYearIdx < len(m.years)-1 {
					m.selectedYearIdx++
				} else {
					m.selectedYearIdx = 0
				}
				m.applyFilter()
				return m, nil
			}

		case "/":
			m.searchInput.Focus()
			m.activePanel = panelList
			return m, textinput.Blink

		case "esc":
			if m.searchInput.Value() != "" {
				m.searchInput.SetValue("")
				m.applyFilter()
				m.statusMsg = "Search cleared"
				return m, nil
			}

		case "tab":
			if m.activePanel == panelList {
				m.activePanel = panelReader
			} else {
				m.activePanel = panelList
			}
			return m, nil

		case "shift+tab":
			if m.activePanel == panelList {
				m.activePanel = panelReader
			} else {
				m.activePanel = panelList
			}
			return m, nil

		case "s":
			// Toggle sort order
			m.sortNewestFirst = !m.sortNewestFirst
			m.applyFilter()
			if m.sortNewestFirst {
				m.statusMsg = "Sorted: Newest First"
			} else {
				m.statusMsg = "Sorted: Oldest First (Chronological)"
			}
			return m, nil

		case "r":
			// Random story
			if len(m.filteredStories) > 0 {
				m.cursor = rand.Intn(len(m.filteredStories))
				m.centerListOnCursor()
				m.updateReaderContent()
				m.statusMsg = fmt.Sprintf("🎲 Random Story: %s", m.filteredStories[m.cursor].Title)
			}
			return m, nil

		case "o":
			// Open in browser
			if len(m.filteredStories) > 0 && m.cursor < len(m.filteredStories) {
				story := m.filteredStories[m.cursor]
				if story.URL != "" {
					_ = openBrowser(story.URL)
					m.statusMsg = fmt.Sprintf("Opening %s in browser...", story.Title)
				}
			}
			return m, nil
		}

		// Panel Specific Navigation
		if m.activePanel == panelList {
			switch msg.String() {
			case "up", "k":
				if m.cursor > 0 {
					m.cursor--
					m.adjustListScroll()
					m.updateReaderContent()
				}
			case "down", "j":
				if m.cursor < len(m.filteredStories)-1 {
					m.cursor++
					m.adjustListScroll()
					m.updateReaderContent()
				}
			case "pageup", "ctrl+u":
				pageSize := m.listVisibleCount()
				m.cursor -= pageSize
				if m.cursor < 0 {
					m.cursor = 0
				}
				m.adjustListScroll()
				m.updateReaderContent()
			case "pagedown", "ctrl+d":
				pageSize := m.listVisibleCount()
				m.cursor += pageSize
				if m.cursor >= len(m.filteredStories) {
					m.cursor = len(m.filteredStories) - 1
				}
				if m.cursor < 0 {
					m.cursor = 0
				}
				m.adjustListScroll()
				m.updateReaderContent()
			case "home", "g":
				m.cursor = 0
				m.adjustListScroll()
				m.updateReaderContent()
			case "end", "G":
				if len(m.filteredStories) > 0 {
					m.cursor = len(m.filteredStories) - 1
					m.adjustListScroll()
					m.updateReaderContent()
				}
			case "enter", "l":
				m.activePanel = panelReader
			}
		} else { // panelReader active
			switch msg.String() {
			case "h":
				m.activePanel = panelList
			case "enter":
				m.activePanel = panelList
			case "up", "k":
				m.viewport.LineUp(1)
			case "down", "j":
				m.viewport.LineDown(1)
			case "pageup", "ctrl+u":
				m.viewport.ViewUp()
			case "pagedown", "ctrl+d", "space":
				m.viewport.ViewDown()
			case "home", "g":
				m.viewport.GotoTop()
			case "end", "G":
				m.viewport.GotoBottom()
			}
		}
	}

	return m, tea.Batch(cmds...)
}

func (m *Model) applyFilter() {
	currentYear := m.years[m.selectedYearIdx]
	m.filteredStories = filterStories(m.allStories, currentYear, m.searchInput.Value(), m.sortNewestFirst)
	if m.cursor >= len(m.filteredStories) {
		m.cursor = 0
	}
	m.listOffset = 0
	m.adjustListScroll()
	m.updateReaderContent()
}

func (m *Model) updateReaderContent() {
	if len(m.filteredStories) == 0 {
		m.viewport.SetContent("No stories found matching your filter criteria.")
		return
	}
	if m.cursor < 0 || m.cursor >= len(m.filteredStories) {
		m.cursor = 0
	}

	story := m.filteredStories[m.cursor]
	readerW := m.readerWidth()
	formatted := formatStoryContent(story, readerW-4)
	m.viewport.SetContent(formatted)
	m.viewport.GotoTop()
}

func (m *Model) adjustListScroll() {
	visibleCount := m.listVisibleCount()
	if visibleCount <= 0 {
		return
	}

	if m.cursor < m.listOffset {
		m.listOffset = m.cursor
	} else if m.cursor >= m.listOffset+visibleCount {
		m.listOffset = m.cursor - visibleCount + 1
	}
}

func (m *Model) centerListOnCursor() {
	visibleCount := m.listVisibleCount()
	m.listOffset = m.cursor - visibleCount/2
	if m.listOffset < 0 {
		m.listOffset = 0
	}
}

func (m Model) listVisibleCount() int {
	contentHeight := m.height - 7
	if m.searchInput.Focused() || m.searchInput.Value() != "" {
		contentHeight -= 2
	}
	if contentHeight < 3 {
		contentHeight = 3
	}
	return contentHeight
}

func (m Model) leftWidth() int {
	if m.width < 90 {
		return m.width - 2
	}
	w := int(float64(m.width) * 0.38)
	if w < 38 {
		w = 38
	}
	if w > 50 {
		w = 50
	}
	return w
}

func (m Model) readerWidth() int {
	if m.width < 90 {
		return m.width - 2
	}
	rw := m.width - m.leftWidth() - 3
	if rw < 40 {
		rw = 40
	}
	return rw
}

func (m Model) View() string {
	if !m.ready || m.width == 0 || m.height == 0 {
		return "Loading Edward W. Pritchard Archives..."
	}

	var mainView string

	// Responsive split
	if m.width < 90 {
		// Single pane view for narrow terminals
		if m.activePanel == panelList {
			mainView = m.renderListPanel(m.width - 2)
		} else {
			mainView = m.renderReaderPanel(m.width - 2)
		}
	} else {
		// Side-by-side view
		leftW := m.leftWidth()
		rightW := m.readerWidth()

		leftView := m.renderListPanel(leftW)
		rightView := m.renderReaderPanel(rightW)

		mainView = lipgloss.JoinHorizontal(lipgloss.Top, leftView, " ", rightView)
	}

	headerView := m.renderHeader()
	statusBarView := m.renderStatusBar()

	fullApp := lipgloss.JoinVertical(lipgloss.Left, headerView, mainView, statusBarView)

	// Overlays
	if m.activeOverlay == overlayYearPicker {
		return m.renderYearPickerModal(fullApp)
	} else if m.activeOverlay == overlayHelp {
		return m.renderHelpModal(fullApp)
	}

	return fullApp
}

func (m Model) renderHeader() string {
	// Demoscene header badge & status info
	banner := styleHeaderBanner.Render("╔═╗╔╦╗  EDWARD W. PRITCHARD ARCHIVE") + " " +
		styleHeaderSub.Render("// DEMO SCENE EDITION")

	currYear := m.years[m.selectedYearIdx]
	var yearTag string
	if currYear == "ALL" {
		yearTag = styleYearActive.Render("YEAR: ALL")
	} else {
		yearTag = styleYearActive.Render(fmt.Sprintf("YEAR: %s", currYear))
	}

	sortTag := lipgloss.NewStyle().Foreground(colorYellow).Render(func() string {
		if m.sortNewestFirst {
			return "[SORT: NEWEST]"
		}
		return "[SORT: CHRONO]"
	}())

	countTag := lipgloss.NewStyle().Foreground(colorGreen).Render(fmt.Sprintf("[%d / %d STORIES]", len(m.filteredStories), len(m.allStories)))

	topRow := banner
	infoRow := fmt.Sprintf("%s  %s  %s  %s",
		yearTag,
		sortTag,
		countTag,
		styleHeaderMeta.Render("• Embedded 2010–2026"),
	)

	return lipgloss.JoinVertical(lipgloss.Left, topRow, infoRow)
}

func (m Model) renderListPanel(width int) string {
	var lines []string

	// Year switcher tabs bar - compact so it never wraps
	currYear := m.years[m.selectedYearIdx]
	var prevYear, nextYear string
	if m.selectedYearIdx > 0 {
		prevYear = m.years[m.selectedYearIdx-1]
	} else {
		prevYear = m.years[len(m.years)-1]
	}
	if m.selectedYearIdx < len(m.years)-1 {
		nextYear = m.years[m.selectedYearIdx+1]
	} else {
		nextYear = m.years[0]
	}

	count := len(m.filteredStories)
	carousel := fmt.Sprintf("◄ %s  %s  %s ►  (%d)",
		styleYearInactive.Render(prevYear),
		styleYearActive.Render(currYear),
		styleYearInactive.Render(nextYear),
		count,
	)
	lines = append(lines, carousel)

	// Search bar if active
	if m.searchInput.Focused() || m.searchInput.Value() != "" {
		lines = append(lines, m.searchInput.View())
	}

	lines = append(lines, lipgloss.NewStyle().Foreground(colorBorder).Render(strings.Repeat("─", width-4)))

	// Items
	visibleCount := m.listVisibleCount()
	total := len(m.filteredStories)

	if total == 0 {
		lines = append(lines, lipgloss.NewStyle().Foreground(colorTextMuted).Render("  No stories found."))
	} else {
		for i := 0; i < visibleCount; i++ {
			idx := m.listOffset + i
			if idx >= total {
				break
			}
			story := m.filteredStories[idx]
			isSelected := idx == m.cursor

			cursorGlyph := "  "
			if isSelected {
				cursorGlyph = "▶ "
			}

			dateStr := story.DateStr
			if len(dateStr) > 10 {
				dateStr = dateStr[:10]
			}

			// Calculate title width: width - borders(2) - padding(2) - glyph(2) - date(10) - space(1)
			remainingW := width - 17
			if remainingW < 10 {
				remainingW = 10
			}

			titleStr := story.Title
			if len([]rune(titleStr)) > remainingW {
				titleStr = string([]rune(titleStr)[:remainingW-1]) + "…"
			} else {
				titleStr = titleStr + strings.Repeat(" ", remainingW-len([]rune(titleStr)))
			}

			var rowStr string
			if isSelected {
				rowStr = styleListSelected.Render(fmt.Sprintf("%s%s %s", cursorGlyph, dateStr, titleStr))
			} else {
				rowStr = fmt.Sprintf("%s%s %s",
					lipgloss.NewStyle().Foreground(colorTextDim).Render(cursorGlyph),
					styleDate.Render(dateStr),
					styleListNormal.Render(titleStr),
				)
			}
			lines = append(lines, rowStr)
		}
	}

	content := strings.Join(lines, "\n")
	panelStyle := stylePanelInactive
	if m.activePanel == panelList {
		panelStyle = stylePanelActive
	}

	return panelStyle.Width(width).Height(m.height - 6).Render(content)
}

func (m Model) renderReaderPanel(width int) string {
	scrollPercent := fmt.Sprintf("[%3.0f%%]", m.viewport.ScrollPercent()*100)
	scrollBadge := lipgloss.NewStyle().Foreground(colorCyan).Render(scrollPercent)

	headerInfo := fmt.Sprintf("%s %s",
		lipgloss.NewStyle().Foreground(colorMagenta).Bold(true).Render("READER"),
		scrollBadge,
	)

	body := lipgloss.JoinVertical(lipgloss.Left, headerInfo, m.viewport.View())

	panelStyle := stylePanelInactive
	if m.activePanel == panelReader {
		panelStyle = stylePanelActive
	}

	return panelStyle.Width(width).Height(m.height - 6).Render(body)
}

func (m Model) renderStatusBar() string {
	var keys []string
	if m.width < 95 {
		keys = append(keys, styleStatusKey.Render("↑/↓")+" "+styleStatusDesc.Render("Nav"))
		keys = append(keys, styleStatusKey.Render("Tab")+" "+styleStatusDesc.Render("Panel"))
		keys = append(keys, styleStatusKey.Render("[/]")+" "+styleStatusDesc.Render("Year"))
		keys = append(keys, styleStatusKey.Render("/")+" "+styleStatusDesc.Render("Find"))
		keys = append(keys, styleStatusKey.Render("r")+" "+styleStatusDesc.Render("Dice"))
		keys = append(keys, styleStatusKey.Render("?")+" "+styleStatusDesc.Render("Help"))
		keys = append(keys, styleStatusKey.Render("q")+" "+styleStatusDesc.Render("Quit"))
	} else {
		keys = append(keys, styleStatusKey.Render("↑/↓ j/k")+" "+styleStatusDesc.Render("Move"))
		keys = append(keys, styleStatusKey.Render("Tab")+" "+styleStatusDesc.Render("Panel"))
		keys = append(keys, styleStatusKey.Render("[ / ]")+" "+styleStatusDesc.Render("Year"))
		keys = append(keys, styleStatusKey.Render("y")+" "+styleStatusDesc.Render("Menu"))
		keys = append(keys, styleStatusKey.Render("/")+" "+styleStatusDesc.Render("Search"))
		keys = append(keys, styleStatusKey.Render("r")+" "+styleStatusDesc.Render("Random"))
		keys = append(keys, styleStatusKey.Render("s")+" "+styleStatusDesc.Render("Sort"))
		keys = append(keys, styleStatusKey.Render("o")+" "+styleStatusDesc.Render("Web"))
		keys = append(keys, styleStatusKey.Render("?")+" "+styleStatusDesc.Render("Help"))
		keys = append(keys, styleStatusKey.Render("q")+" "+styleStatusDesc.Render("Quit"))
	}

	leftInfo := strings.Join(keys, " ")

	rightInfo := ""
	if m.statusMsg != "" {
		rightInfo = lipgloss.NewStyle().Foreground(colorYellow).Bold(true).Render(m.statusMsg)
	} else if len(m.filteredStories) > 0 {
		rightInfo = fmt.Sprintf("Story %d of %d", m.cursor+1, len(m.filteredStories))
	}

	gap := m.width - lipgloss.Width(leftInfo) - lipgloss.Width(rightInfo) - 2
	if gap < 1 {
		gap = 1
	}

	return styleStatusBar.Width(m.width).Render(leftInfo + strings.Repeat(" ", gap) + rightInfo)
}

func (m Model) renderYearPickerModal(bg string) string {
	var rows []string
	rows = append(rows, lipgloss.NewStyle().Bold(true).Foreground(colorMagenta).Render("◈ SELECT STORY YEAR ◈"))
	rows = append(rows, lipgloss.NewStyle().Foreground(colorTextDim).Render("─────────────────────────────────"))

	for i, yName := range m.years {
		count := len(m.allStories)
		if yName != "ALL" {
			count = m.yearCounts[yName]
		}

		cursor := "  "
		if i == m.yearPickerCursor {
			cursor = "▶ "
		}

		label := fmt.Sprintf("%-6s (%d stories)", yName, count)
		if i == m.yearPickerCursor {
			rows = append(rows, styleListSelected.Render(cursor+label))
		} else {
			rows = append(rows, styleListNormal.Render(cursor+label))
		}
	}

	rows = append(rows, lipgloss.NewStyle().Foreground(colorTextDim).Render("─────────────────────────────────"))
	rows = append(rows, styleStatusDesc.Render("[Enter] Select  [Esc/y] Close"))

	modalContent := styleModal.Render(strings.Join(rows, "\n"))
	return lipgloss.Place(m.width, m.height, lipgloss.Center, lipgloss.Center, modalContent, lipgloss.WithWhitespaceChars(" "))
}

func (m Model) renderHelpModal(bg string) string {
	var rows []string
	rows = append(rows, styleHeaderBanner.Render(demosceneLogo))
	rows = append(rows, "")
	rows = append(rows, lipgloss.NewStyle().Bold(true).Foreground(colorCyan).Render("EDWARD W. PRITCHARD // DEMO SCENE STORY ARCHIVE"))
	rows = append(rows, lipgloss.NewStyle().Foreground(colorTextDim).Render("══════════════════════════════════════════════════════"))
	rows = append(rows, styleStatusKey.Render("j / k / ↑ / ↓      ")+"Navigate list / scroll reader")
	rows = append(rows, styleStatusKey.Render("Tab / Shift+Tab    ")+"Switch between Story List and Reader")
	rows = append(rows, styleStatusKey.Render("Enter              ")+"Select / focus reader")
	rows = append(rows, styleStatusKey.Render("[ / ] or ← / →     ")+"Cycle years instantly")
	rows = append(rows, styleStatusKey.Render("y                  ")+"Open Year Picker menu")
	rows = append(rows, styleStatusKey.Render("/                  ")+"Search filter by title, tag, or text")
	rows = append(rows, styleStatusKey.Render("Esc                ")+"Clear search filter / close modal")
	rows = append(rows, styleStatusKey.Render("r                  ")+"🎲 Random story (demoscene dice roll)")
	rows = append(rows, styleStatusKey.Render("s                  ")+"Toggle Chronological / Reverse order")
	rows = append(rows, styleStatusKey.Render("o                  ")+"Open original Blogspot story in web browser")
	rows = append(rows, styleStatusKey.Render("PageUp / PageDown  ")+"Fast page scroll")
	rows = append(rows, styleStatusKey.Render("g / G              ")+"Jump to top / bottom")
	rows = append(rows, styleStatusKey.Render("q / Ctrl+C         ")+"Quit application")
	rows = append(rows, lipgloss.NewStyle().Foreground(colorTextDim).Render("══════════════════════════════════════════════════════"))
	rows = append(rows, styleStatusDesc.Render("Press [Esc] or [?] or [Enter] to return"))

	modalContent := styleModal.Render(strings.Join(rows, "\n"))
	return lipgloss.Place(m.width, m.height, lipgloss.Center, lipgloss.Center, modalContent, lipgloss.WithWhitespaceChars(" "))
}

func openBrowser(url string) error {
	var cmd string
	var args []string
	switch runtime.GOOS {
	case "darwin":
		cmd = "open"
		args = []string{url}
	case "windows":
		cmd = "rundll32"
		args = []string{"url.dll,FileProtocolHandler", url}
	default:
		cmd = "xdg-open"
		args = []string{url}
	}
	return exec.Command(cmd, args...).Start()
}
