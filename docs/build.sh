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

rm -rf "$SCRIPT_DIR/_build"
mkdir -p "$SCRIPT_DIR/_build/html"

for LANG_CODE in en jp; do
    LANG_DIR="$SCRIPT_DIR/$LANG_CODE"
    rm -rf "$LANG_DIR/api"
    mkdir -p "$LANG_DIR/api"
    sphinx-apidoc -o "$LANG_DIR/api" "$SRC_DIR/$PKG_NAME" -f --module-first
    sphinx-build -b html "$LANG_DIR" "$SCRIPT_DIR/_build/html/$LANG_CODE"
done

cat > "$SCRIPT_DIR/_build/html/index.html" <<'HTML'
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=./en/">
<link rel="canonical" href="./en/"><title>image_server documentation</title>
</head><body><p><a href="./en/">English</a> / <a href="./jp/">日本語</a></p></body></html>
HTML
: > "$SCRIPT_DIR/_build/html/.nojekyll"
echo "Built: $SCRIPT_DIR/_build/html/{en,jp}/"
