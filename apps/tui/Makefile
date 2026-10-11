.PHONY: all build build-linux run sync test clean install

BINARY_NAME=ed-tui
LINUX_BINARY_NAME=ed-tui-linux-amd64

all: build

# Sync markdown story files from repo root into local embed content directory
sync:
	mkdir -p content
	rsync -av --exclude="README.md" --include="20*/" --include="20*/*.md" --exclude="*" ../../ content/

# Build standalone binary with all stories embedded (host architecture)
build: sync
	go build -ldflags="-s -w" -o $(BINARY_NAME) .

# Build standalone static binary for Linux server (x86_64 / amd64)
build-linux: sync
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w" -o $(LINUX_BINARY_NAME) .

# Build multi-platform release binaries and SHA-256 checksums in dist/
release: sync
	@echo "Building release binaries..."
	mkdir -p dist
	CGO_ENABLED=0 GOOS=darwin  GOARCH=arm64 go build -ldflags="-s -w" -o dist/ed-tui-darwin-arm64 .
	CGO_ENABLED=0 GOOS=darwin  GOARCH=amd64 go build -ldflags="-s -w" -o dist/ed-tui-darwin-amd64 .
	CGO_ENABLED=0 GOOS=linux   GOARCH=amd64 go build -ldflags="-s -w" -o dist/ed-tui-linux-amd64 .
	CGO_ENABLED=0 GOOS=linux   GOARCH=arm64 go build -ldflags="-s -w" -o dist/ed-tui-linux-arm64 .
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o dist/ed-tui-windows-amd64.exe .
	@echo "Generating SHA-256 checksums..."
	cd dist && (command -v sha256sum >/dev/null 2>&1 && sha256sum ed-tui-* || shasum -a 256 ed-tui-*) > checksums.txt
	@echo "Release build complete! Assets located in dist/:"
	@ls -lh dist

# Run the TUI locally
run: build
	./$(BINARY_NAME)

# Run tests
test:
	go test -v ./...

# Install to GOPATH/bin
install: build
	go install

clean:
	rm -rf $(BINARY_NAME) $(LINUX_BINARY_NAME) dist
