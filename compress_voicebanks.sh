#!/usr/bin/env bash
set -u

THRESHOLD=99999999

find . -type f -name "*.xwb" | while IFS= read -r file; do
    echo "Compressing: $file"
    dir=$(dirname "$file")
    base=$(basename "$file")

    (
        cd "$dir" || exit 1

        tmp_zip="${base}.tmp.zip"
        rm -f "$tmp_zip" "$base.zip" "$base.zip."*

        if zip -9 -q "$tmp_zip" "$base"; then
            zip_size=$(wc -c < "$tmp_zip" | tr -d ' ')

            if [ "$zip_size" -gt "$THRESHOLD" ]; then
                if split -b "$THRESHOLD" -d -a 3 "$tmp_zip" "$base.zip."; then
                    rm -f "$tmp_zip"
                else
                    echo "ERROR: Splitting failed for $file. Archive cleaned up." >&2
                    rm -f "$base.zip."* "$tmp_zip"
                fi
            else
                if ! mv "$tmp_zip" "$base.zip"; then
                    echo "ERROR: Finalizing zip failed for $file." >&2
                    rm -f "$tmp_zip"
                fi
            fi
        else
            echo "ERROR: Compression failed for $file." >&2
            rm -f "$tmp_zip"
        fi
    )
done

echo ""
read -n 1 -s -r -p "Press any key to continue..."
echo ""