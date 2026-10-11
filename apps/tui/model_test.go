package main

import (
	"testing"

	tea "github.com/charmbracelet/bubbletea"
)

func TestModelRenderAndKeys(t *testing.T) {
	stories, err := loadAllStories()
	if err != nil {
		t.Fatalf("Failed to load stories: %v", err)
	}
	if len(stories) == 0 {
		t.Fatalf("No stories found")
	}

	m := initialModel(stories)

	// Test window sizes: normal, large, narrow
	sizes := [][2]int{
		{120, 40},
		{80, 24},
		{60, 20},
		{160, 50},
	}

	for _, sz := range sizes {
		updated, _ := m.Update(tea.WindowSizeMsg{Width: sz[0], Height: sz[1]})
		m = updated.(Model)
		view := m.View()
		if len(view) == 0 {
			t.Errorf("Empty view at size %dx%d", sz[0], sz[1])
		}
	}

	// Test navigation down/up
	updated, _ := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'j'}})
	m = updated.(Model)
	if m.cursor != 1 {
		t.Errorf("Expected cursor 1, got %d", m.cursor)
	}

	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'k'}})
	m = updated.(Model)
	if m.cursor != 0 {
		t.Errorf("Expected cursor 0, got %d", m.cursor)
	}

	// Test random story
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}})
	m = updated.(Model)

	// Test panel switch
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyTab})
	m = updated.(Model)
	if m.activePanel != panelReader {
		t.Errorf("Expected panelReader, got %v", m.activePanel)
	}

	// Reader navigation
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'j'}})
	m = updated.(Model)
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'k'}})
	m = updated.(Model)
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'h'}})
	m = updated.(Model)
	if m.activePanel != panelList {
		t.Errorf("Expected panelList after pressing h, got %v", m.activePanel)
	}

	// Test sort toggle
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'s'}})
	m = updated.(Model)
	if !m.sortNewestFirst {
		t.Errorf("Expected sortNewestFirst to be true")
	}

	// Test year cycling
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{']'}})
	m = updated.(Model)
	if m.selectedYearIdx == 0 {
		t.Errorf("Expected selectedYearIdx to advance past 0")
	}

	// Test search
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'/'}})
	m = updated.(Model)
	if !m.searchInput.Focused() {
		t.Errorf("Expected search input to be focused")
	}
	m.searchInput.SetValue("albert")
	m.applyFilter()
	if len(m.filteredStories) == 0 {
		t.Errorf("Expected matches for query 'albert'")
	}

	// Clear search with Esc
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyEsc})
	m = updated.(Model)
	if m.searchInput.Focused() {
		t.Errorf("Expected search input to be unfocused after Esc")
	}

	// Test year picker modal
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'y'}})
	m = updated.(Model)
	if m.activeOverlay != overlayYearPicker {
		t.Errorf("Expected overlayYearPicker, got %v", m.activeOverlay)
	}

	viewModal := m.View()
	if len(viewModal) == 0 {
		t.Errorf("Empty modal view")
	}

	// Close year picker
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyEsc})
	m = updated.(Model)
	if m.activeOverlay != overlayNone {
		t.Errorf("Expected overlayNone, got %v", m.activeOverlay)
	}

	// Test help modal
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'?'}})
	m = updated.(Model)
	if m.activeOverlay != overlayHelp {
		t.Errorf("Expected overlayHelp, got %v", m.activeOverlay)
	}

	viewHelp := m.View()
	if len(viewHelp) == 0 {
		t.Errorf("Empty help view")
	}

	// Close help
	updated, _ = m.Update(tea.KeyMsg{Type: tea.KeyEsc})
	m = updated.(Model)
	if m.activeOverlay != overlayNone {
		t.Errorf("Expected overlayNone, got %v", m.activeOverlay)
	}
}
