#!/usr/bin/env bash
set -euo pipefail

# deploy.sh
# Packages the apps/gh-pages static archive (HTML, CSS, JS, JSON, and stories)
# directly into a local 'gh-pages' branch for deployment on GitHub Pages.
#
# Can be run from apps/gh-pages/ or the repository root.
#
# Usage:
#   ./deploy.sh                  # Commit apps/gh-pages directly to local gh-pages branch
#   ./deploy.sh --push           # Commit and push gh-pages branch to origin
#   ./deploy.sh --build          # Run python3 build.py first, then commit
#   ./deploy.sh -m "Custom msg"  # Specify a custom commit message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)"
GH_PAGES_SRC="$REPO_ROOT/apps/gh-pages"

BRANCH="gh-pages"
DO_PUSH=false
DO_BUILD=false
ORPHAN=false
CUSTOM_MSG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--push)
            DO_PUSH=true
            shift
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -m|--message)
            CUSTOM_MSG="$2"
            shift 2
            ;;
        -o|--orphan)
            ORPHAN=true
            shift
            ;;
        --build)
            DO_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -p, --push            Push branch to remote 'origin' after committing"
            echo "  -b, --branch <name>   Target branch name (default: gh-pages)"
            echo "  -m, --message <msg>   Custom commit message"
            echo "  -o, --orphan          Create fresh orphan commit without parent history"
            echo "  --build               Run build.py to regenerate HTML before committing"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Run '$0 --help' for usage." >&2
            exit 1
            ;;
    esac
done

if [ ! -d "$GH_PAGES_SRC" ]; then
    echo "Error: Directory '$GH_PAGES_SRC' does not exist." >&2
    exit 1
fi

# Rebuild if requested or if index.html is missing
if [ "$DO_BUILD" = true ] || [ ! -f "$GH_PAGES_SRC/index.html" ]; then
    echo "Building static site in $GH_PAGES_SRC..."
    python3 "$GH_PAGES_SRC/build.py"
fi

if [ ! -f "$GH_PAGES_SRC/index.html" ]; then
    echo "Error: index.html not found in $GH_PAGES_SRC. Run 'python3 build.py' first." >&2
    exit 1
fi

STORY_PAGES=$(find "$GH_PAGES_SRC/stories" -name "*.html" 2>/dev/null | wc -l | tr -d ' ')
echo "Found $STORY_PAGES story pages in $GH_PAGES_SRC/stories."
echo "Packaging static site into branch '$BRANCH'..."

# Create isolated temporary staging directory and independent git index
TMP_DIR=$(mktemp -d)
INDEX_FILE=$(mktemp -u)

cleanup() {
    rm -rf "$TMP_DIR"
    rm -f "$INDEX_FILE"
}
trap cleanup EXIT

# Copy all static assets into temporary directory
cp -R "$GH_PAGES_SRC"/* "$TMP_DIR"/

# Ensure GitHub Pages Jekyll bypass marker exists
touch "$TMP_DIR/.nojekyll"

# Remove developer tooling from published web branch
rm -f "$TMP_DIR/build.py" "$TMP_DIR/Makefile" "$TMP_DIR/deploy.sh" "$TMP_DIR/package-pages.sh"
find "$TMP_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$TMP_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$TMP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Prepare git plumbing environment
GIT_DIR="$(git -C "$REPO_ROOT" rev-parse --absolute-git-dir)"
export GIT_DIR
export GIT_WORK_TREE="$TMP_DIR"
export GIT_INDEX_FILE="$INDEX_FILE"

git add -A -f
TREE_ID=$(git write-tree)

TIMESTAMP=$(date -u +'%Y-%m-%d %H:%M:%S UTC')
DEFAULT_MSG="Deploy Edward W. Pritchard Writings archive ($TIMESTAMP)"
COMMIT_MSG="${CUSTOM_MSG:-$DEFAULT_MSG}"

# Determine parent commit unless orphan mode requested
COMMIT_ID=""
if [ "$ORPHAN" = false ] && git -C "$REPO_ROOT" rev-parse --verify "refs/heads/$BRANCH" >/dev/null 2>&1; then
    PARENT_COMMIT="$(git -C "$REPO_ROOT" rev-parse "refs/heads/$BRANCH")"
    PARENT_TREE="$(git -C "$REPO_ROOT" rev-parse "$PARENT_COMMIT^{tree}" 2>/dev/null || true)"
    if [ "$PARENT_TREE" = "$TREE_ID" ]; then
        echo "No changes detected in $GH_PAGES_SRC since last commit ($PARENT_COMMIT)."
        COMMIT_ID="$PARENT_COMMIT"
    else
        COMMIT_ID=$(git commit-tree "$TREE_ID" -p "$PARENT_COMMIT" -m "$COMMIT_MSG")
        git -C "$REPO_ROOT" update-ref "refs/heads/$BRANCH" "$COMMIT_ID"
    fi
else
    COMMIT_ID=$(git commit-tree "$TREE_ID" -m "$COMMIT_MSG")
    git -C "$REPO_ROOT" update-ref "refs/heads/$BRANCH" "$COMMIT_ID"
fi

TOTAL_FILES=$(find "$TMP_DIR" -type f | wc -l | tr -d ' ')

echo "------------------------------------------------------------"
echo "Successfully committed static site to '$BRANCH' branch!"
echo "  Commit:       $COMMIT_ID"
echo "  Total files:  $TOTAL_FILES"
echo "  Story pages:  $STORY_PAGES"
echo "  Message:      $COMMIT_MSG"
echo "------------------------------------------------------------"

if [ "$DO_PUSH" = true ]; then
    if git -C "$REPO_ROOT" remote get-url origin >/dev/null 2>&1; then
        echo "Pushing '$BRANCH' to origin..."
        git -C "$REPO_ROOT" push -u origin "$BRANCH"
        echo "Push complete!"
    else
        echo "Warning: Remote 'origin' is not configured yet." >&2
        echo "Add remote via: git remote add origin <repo-url>" >&2
        echo "Then push via:  git push -u origin $BRANCH" >&2
    fi
else
    echo "To push this branch to GitHub:"
    echo "    git push -u origin $BRANCH"
    echo ""
    echo "GitHub Pages configuration:"
    echo "  1. In repository settings: Settings -> Pages"
    echo "  2. Under 'Build and deployment' > 'Source': select 'Deploy from a branch'"
    echo "  3. Select branch '$BRANCH' and folder '/ (root)'"
    echo "  4. Save; GitHub Pages will deploy the static archive at your github.io URL"
fi
