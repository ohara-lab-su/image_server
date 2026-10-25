#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$ROOT_DIR/src"
PKG_NAME="image_server"

export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

if [[ ! -d "$SRC_DIR/$PKG_NAME" ]]; then
    echo "Package directory not found: $SRC_DIR/$PKG_NAME" >&2
    exit 1
fi

rm -rf "$SCRIPT_DIR/_build" "$SCRIPT_DIR/en/api" "$SCRIPT_DIR/ja/api"

for LANG_CODE in en ja; do
    sphinx-apidoc -o "$SCRIPT_DIR/$LANG_CODE/api" "$SRC_DIR/$PKG_NAME" -f --module-first
    sphinx-build -b html -c "$SCRIPT_DIR" -D "language=$LANG_CODE" \
        "$SCRIPT_DIR/$LANG_CODE" "$SCRIPT_DIR/_build/html/$LANG_CODE"
done

# Build the site root from docs/index.md, without overwriting docs/en/index.md.
# Use a separate temporary source tree so relative paths remain those of en/.
ROOT_SOURCE="$(mktemp -d)"
trap 'rm -rf "$ROOT_SOURCE"' EXIT
cp -R "$SCRIPT_DIR/en/." "$ROOT_SOURCE/"
cp "$SCRIPT_DIR/index.md" "$ROOT_SOURCE/index.md"
sphinx-build -b html -c "$SCRIPT_DIR" -D language=en \
    "$ROOT_SOURCE" "$SCRIPT_DIR/_build/html"
: > "$SCRIPT_DIR/_build/html/.nojekyll"
echo "Built English at / and /en/; Japanese at /ja/"
