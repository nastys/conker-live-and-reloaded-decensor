#!/usr/bin/env bash
set -u

find . -type f \( -name "*.xwb.zip.000" -o -name "*.xwb.zip.001" \) | while IFS= read -r first_part; do
    [ -f "$first_part" ] || continue

    dir=$(dirname "$first_part")
    zipfile="${first_part%.*}"
    base_zip=$(basename "$zipfile")
    echo "Decompressing split archive: $zipfile"
    (
        cd "$dir" || exit 1
        tmp_zip="${base_zip}.tmp"
        
        if cat "$base_zip."* > "$tmp_zip"; then
            if unzip -o -q "$tmp_zip"; then
                rm -f "$base_zip."* "$tmp_zip"
            else
                echo "ERROR: Extraction failed for split archive $zipfile. Archive preserved." >&2
                rm -f "$tmp_zip"
            fi
        else
            echo "ERROR: Reassembling split archive failed for $zipfile." >&2
            rm -f "$tmp_zip"
        fi
    )
done

find . -type f -name "*.xwb.zip" | while IFS= read -r zipfile; do
    [ -f "$zipfile" ] || continue

    dir=$(dirname "$zipfile")
    base_zip=$(basename "$zipfile")
    echo "Decompressing: $zipfile"
    (
        cd "$dir" || exit 1
        if unzip -o -q "$base_zip"; then
            rm -f "$base_zip"
        else
            echo "ERROR: Extraction failed for $zipfile. Archive preserved." >&2
        fi
    )
done

echo ""
read -n 1 -s -r -p "Press any key to continue..."
echo ""