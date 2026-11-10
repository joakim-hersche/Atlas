#!/usr/bin/env bash
# Publish web/dist to the gh-pages branch of this repository (GitHub Pages, decision D33).
# The branch holds only the built site and is replaced on every deploy (one commit, no history),
# so built data never accumulates in git. Run `make web-data web-app` first.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/web/dist"
[ -f "$DIST/index.html" ] || { echo "no build in web/dist: run make web-data web-app" >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp -r "$DIST/." "$TMP/"
find "$TMP" -name .gitkeep -delete
touch "$TMP/.nojekyll"
cd "$TMP"
git init -q -b gh-pages
git config user.name "${GIT_AUTHOR_NAME:-Claude}"
git config user.email "${GIT_AUTHOR_EMAIL:-noreply@anthropic.com}"
git add -A
git commit -q -m "Deploy Gemeindebank site (built from $(git -C "$ROOT" rev-parse --short HEAD))"
git push -f "$(git -C "$ROOT" remote get-url origin)" gh-pages:gh-pages
echo "deployed to gh-pages"
