#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCES_DIR="$ROOT_DIR/plugins/sources"
OUTPUT_DIR="${1:-$ROOT_DIR/plugins/build}"

if [[ ! -d "$SOURCES_DIR" ]]; then
  echo "Missing plugin sources directory: $SOURCES_DIR"
  exit 1
fi

for plugin_dir in "$SOURCES_DIR"/*; do
  if [[ ! -d "$plugin_dir" ]]; then
    continue
  fi

  plugin_name="$(basename "$plugin_dir")"
  "$ROOT_DIR/scripts/build_plugin.sh" "$plugin_name" "$plugin_dir" "$OUTPUT_DIR"
done

echo "All plugins built in $OUTPUT_DIR"
