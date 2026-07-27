#!/bin/bash

ROOT_DIR="${1:-.}"
TOOL_PATH="caff_tool.py"

echo "Recursively packing 'default.toml' -> 'default.bin' in '$ROOT_DIR'..."
find "$ROOT_DIR" -type f -name "default.toml" -print0 | while IFS= read -r -d '' toml_file; do
    dir=$(dirname "$toml_file")
    bin_file="$dir/default.bin"
    echo "Packing: $toml_file -> $bin_file"
    python "$TOOL_PATH" pack "$toml_file" "$bin_file"  --safe
done

echo ""
read -n 1 -s -r -p "Press any key to continue..."
echo ""