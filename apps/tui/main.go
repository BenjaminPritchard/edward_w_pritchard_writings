package main

import (
	"flag"
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
)

var (
	version = "1.0.0"
)

func main() {
	showVersion := flag.Bool("version", false, "print version and exit")
	flag.BoolVar(showVersion, "v", false, "print version and exit")
	preview := flag.Bool("preview", false, "render single screen snapshot to stdout and exit")
	flag.Parse()

	if *showVersion {
		fmt.Printf("ed-tui %s - Edward W. Pritchard Story Archive\n", version)
		os.Exit(0)
	}

	stories, err := loadAllStories()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading embedded stories: %v\n", err)
		os.Exit(1)
	}

	if len(stories) == 0 {
		fmt.Fprintf(os.Stderr, "No embedded stories found.\n")
		os.Exit(1)
	}

	m := initialModel(stories)

	if *preview {
		updated, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 30})
		m = updated.(Model)
		fmt.Println(m.View())
		os.Exit(0)
	}
	p := tea.NewProgram(
		m,
		tea.WithAltScreen(),
		tea.WithMouseCellMotion(),
	)

	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error running ed-tui: %v\n", err)
		os.Exit(1)
	}
}
