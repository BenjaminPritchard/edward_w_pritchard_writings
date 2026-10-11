#!/usr/bin/env bash
# Root runner to deploy apps/gh-pages directly to local gh-pages branch
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/apps/gh-pages/deploy.sh" "$@"
