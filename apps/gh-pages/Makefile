# Edward W. Pritchard Stories Archive - gh-pages static site Makefile

.PHONY: all build serve deploy push clean help

all: build

build:
	@echo "Building static site..."
	@python3 build.py

serve:
	@echo "Starting local HTTP server on http://localhost:8080..."
	@python3 -m http.server 8080

deploy:
	@./deploy.sh

push:
	@./deploy.sh --push

clean:
	@echo "Cleaning generated HTML files and data..."
	@rm -rf stories years index.html stories.json js/stories-data.js
	@echo "Done."

help:
	@echo "Available targets:"
	@echo "  make build   - Regenerate static HTML site and search index"
	@echo "  make serve   - Preview site locally on http://localhost:8080"
	@echo "  make deploy  - Commit static archive directly to local gh-pages branch"
	@echo "  make push    - Commit and push gh-pages branch to origin"
	@echo "  make clean   - Remove generated HTML pages"
