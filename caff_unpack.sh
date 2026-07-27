#!/bin/bash

ROOT_DIR="${1:-.}"
TOOL_PATH="caff_tool.py"

echo "Recursively unpacking 'default.bin' -> 'default.toml' in '$ROOT_DIR'..."
find "$ROOT_DIR" -type f -name "default.bin" -print0 | while IFS= read -r -d '' bin_file; do
    dir=$(dirname "$bin_file")
    toml_file="$dir/default.toml"
    echo "Unpacking: $bin_file -> $toml_file"
    python "$TOOL_PATH" unpack "$bin_file" "$toml_file"
done
