package main

import (
	"bufio"
	"embed"
	"fmt"
	"io/fs"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
)

//go:embed content/*/*.md
var embeddedFS embed.FS

type Story struct {
	ID          string
	Title       string
	DateStr     string
	Date        time.Time
	Year        string
	Author      string
	URL         string
	PostID      string
	Categories  []string
	Body        string
	WordCount   int
	ReadMinutes int
	FilePath    string
}

func loadAllStories() ([]Story, error) {
	var stories []Story

	err := fs.WalkDir(embeddedFS, "content", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !strings.HasSuffix(path, ".md") {
			return nil
		}

		data, err := embeddedFS.ReadFile(path)
		if err != nil {
			return err
		}

		story := parseStory(path, data)
		stories = append(stories, story)
		return nil
	})

	if err != nil {
		return nil, err
	}

	// Sort chronologically by date ascending by default
	sort.Slice(stories, func(i, j int) bool {
		if stories[i].Date.Equal(stories[j].Date) {
			return stories[i].Title < stories[j].Title
		}
		return stories[i].Date.Before(stories[j].Date)
	})

	return stories, nil
}

func parseStory(path string, data []byte) Story {
	content := string(data)
	s := Story{
		FilePath: path,
		ID:       strings.TrimSuffix(filepath.Base(path), ".md"),
	}

	parts := strings.SplitN(content, "---", 3)
	if len(parts) >= 3 {
		frontmatter := parts[1]
		s.Body = strings.TrimSpace(parts[2])

		scanner := bufio.NewScanner(strings.NewReader(frontmatter))
		inCategories := false

		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" {
				continue
			}

			if strings.HasPrefix(line, "title:") {
				inCategories = false
				s.Title = cleanYAMLVal(strings.TrimPrefix(line, "title:"))
			} else if strings.HasPrefix(line, "date:") {
				inCategories = false
				dateVal := cleanYAMLVal(strings.TrimPrefix(line, "date:"))
				s.DateStr = dateVal
				if len(dateVal) >= 10 {
					s.DateStr = dateVal[:10]
					s.Year = dateVal[:4]
				}
				if t, err := time.Parse(time.RFC3339, dateVal); err == nil {
					s.Date = t
				}
			} else if strings.HasPrefix(line, "author:") {
				inCategories = false
				s.Author = cleanYAMLVal(strings.TrimPrefix(line, "author:"))
			} else if strings.HasPrefix(line, "url:") {
				inCategories = false
				s.URL = cleanYAMLVal(strings.TrimPrefix(line, "url:"))
			} else if strings.HasPrefix(line, "post_id:") {
				inCategories = false
				s.PostID = cleanYAMLVal(strings.TrimPrefix(line, "post_id:"))
			} else if strings.HasPrefix(line, "categories:") {
				val := strings.TrimSpace(strings.TrimPrefix(line, "categories:"))
				if val == "[]" || val == "" {
					inCategories = (val == "")
				} else if strings.HasPrefix(val, "[") && strings.HasSuffix(val, "]") {
					items := strings.Split(val[1:len(val)-1], ",")
					for _, it := range items {
						c := cleanYAMLVal(it)
						if c != "" {
							s.Categories = append(s.Categories, c)
						}
					}
				}
			} else if inCategories && strings.HasPrefix(line, "-") {
				c := cleanYAMLVal(strings.TrimPrefix(line, "-"))
				if c != "" {
					s.Categories = append(s.Categories, c)
				}
			} else if !strings.HasPrefix(line, " ") && !strings.HasPrefix(line, "\t") {
				inCategories = false
			}
		}
	} else {
		s.Body = content
	}

	if s.Title == "" {
		s.Title = strings.ReplaceAll(s.ID, "-", " ")
	}
	if s.Author == "" {
		s.Author = "Edward W. Pritchard"
	}
	if s.Year == "" && len(s.DateStr) >= 4 {
		s.Year = s.DateStr[:4]
	}

	words := strings.Fields(s.Body)
	s.WordCount = len(words)
	s.ReadMinutes = (s.WordCount + 150) / 200
	if s.ReadMinutes < 1 {
		s.ReadMinutes = 1
	}

	return s
}

func cleanYAMLVal(s string) string {
	s = strings.TrimSpace(s)
	s = strings.Trim(s, `"'`)
	return strings.TrimSpace(s)
}

func filterStories(all []Story, yearFilter string, searchQuery string, newestFirst bool) []Story {
	query := strings.ToLower(strings.TrimSpace(searchQuery))
	isAllYear := yearFilter == "" || yearFilter == "ALL"

	var filtered []Story
	for _, s := range all {
		if !isAllYear && s.Year != yearFilter {
			continue
		}

		if query != "" {
			match := strings.Contains(strings.ToLower(s.Title), query) ||
				strings.Contains(strings.ToLower(s.DateStr), query)
			if !match {
				for _, cat := range s.Categories {
					if strings.Contains(strings.ToLower(cat), query) {
						match = true
						break
					}
				}
			}
			if !match && strings.Contains(strings.ToLower(s.Body), query) {
				match = true
			}
			if !match {
				continue
			}
		}

		filtered = append(filtered, s)
	}

	// Sort
	sort.Slice(filtered, func(i, j int) bool {
		if newestFirst {
			if filtered[i].Date.Equal(filtered[j].Date) {
				return filtered[i].Title < filtered[j].Title
			}
			return filtered[i].Date.After(filtered[j].Date)
		}
		if filtered[i].Date.Equal(filtered[j].Date) {
			return filtered[i].Title < filtered[j].Title
		}
		return filtered[i].Date.Before(filtered[j].Date)
	})

	return filtered
}

func formatStoryContent(s Story, width int) string {
	if width <= 10 {
		width = 60
	}
	contentWidth := width - 4
	if contentWidth < 30 {
		contentWidth = 30
	}

	var sb strings.Builder

	// Header Box
	titleStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(colorMagenta).
		Width(contentWidth)

	metaStyle := lipgloss.NewStyle().
		Foreground(colorCyan)

	tagStyle := lipgloss.NewStyle().
		Foreground(colorPurple).
		Background(lipgloss.Color("#271d3d")).
		Padding(0, 1)

	linkStyle := lipgloss.NewStyle().
		Foreground(colorBlue)

	sb.WriteString(titleStyle.Render(strings.ToUpper(s.Title)))
	sb.WriteString("\n")

	// Meta row
	metaStr := fmt.Sprintf("📅 %s  •  📖 %d words (~%d min read)  •  ✍️ %s",
		s.DateStr, s.WordCount, s.ReadMinutes, s.Author)
	sb.WriteString(metaStyle.Render(metaStr))
	sb.WriteString("\n")

	// Categories row
	if len(s.Categories) > 0 {
		var tags []string
		for _, cat := range s.Categories {
			tags = append(tags, tagStyle.Render("#"+cat))
		}
		sb.WriteString("🏷️  " + strings.Join(tags, " "))
		sb.WriteString("\n")
	}

	if s.URL != "" {
		displayURL := s.URL
		if len(displayURL) > contentWidth-4 && contentWidth > 15 {
			displayURL = displayURL[:contentWidth-7] + "..."
		}
		sb.WriteString(linkStyle.Render("🔗 " + displayURL))
		sb.WriteString("\n")
	}

	// Demoscene Divider
	divLine := strings.Repeat("─", contentWidth)
	sb.WriteString(lipgloss.NewStyle().Foreground(colorBorder).Render(divLine))
	sb.WriteString("\n\n")

	// Clean body
	lines := strings.Split(s.Body, "\n")
	skipFirstTitle := true

	h1Style := lipgloss.NewStyle().Bold(true).Foreground(colorCyan).Width(contentWidth)
	h2Style := lipgloss.NewStyle().Bold(true).Foreground(colorYellow).Width(contentWidth)
	quoteStyle := lipgloss.NewStyle().Foreground(colorTextMuted).Italic(true).BorderLeft(true).BorderStyle(lipgloss.NormalBorder()).BorderForeground(colorPurple).PaddingLeft(1)
	bodyStyle := lipgloss.NewStyle().Foreground(colorTextBright).Width(contentWidth)
	subheadStyle := lipgloss.NewStyle().Foreground(colorTextMuted).Italic(true)

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Skip duplicate title at the top
		if skipFirstTitle && (strings.HasPrefix(trimmed, "# ") || strings.EqualFold(trimmed, s.Title)) {
			skipFirstTitle = false
			continue
		}
		skipFirstTitle = false

		if trimmed == "" {
			sb.WriteString("\n")
			continue
		}

		if strings.HasPrefix(trimmed, "## ") {
			sb.WriteString(h2Style.Render(strings.TrimPrefix(trimmed, "## ")))
			sb.WriteString("\n\n")
		} else if strings.HasPrefix(trimmed, "# ") {
			sb.WriteString(h1Style.Render(strings.TrimPrefix(trimmed, "# ")))
			sb.WriteString("\n\n")
		} else if strings.HasPrefix(trimmed, "> ") {
			sb.WriteString(quoteStyle.Render(strings.TrimPrefix(trimmed, "> ")))
			sb.WriteString("\n")
		} else if strings.EqualFold(trimmed, "fiction") || strings.EqualFold(trimmed, s.Author) || strings.EqualFold(trimmed, "edward w pritchard") {
			sb.WriteString(subheadStyle.Render("  " + trimmed))
			sb.WriteString("\n")
		} else {
			sb.WriteString(bodyStyle.Render(trimmed))
			sb.WriteString("\n\n")
		}
	}

	// Demoscene End Marker
	sb.WriteString("\n")
	endBanner := lipgloss.NewStyle().
		Foreground(colorMagenta).
		Bold(true).
		Align(lipgloss.Center).
		Width(contentWidth).
		Render("◈ ◈ ◈  [ END OF STORY ]  ◈ ◈ ◈\nEDWARD W. PRITCHARD ARCHIVES")
	sb.WriteString(endBanner)
	sb.WriteString("\n")

	return sb.String()
}
