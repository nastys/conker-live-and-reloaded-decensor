import sys
import struct
import json
import re

try:
    import tomllib
except ImportError:
    print("Error: Python 3.11 or higher is required.")
    sys.exit(1)


class CaffTomlConverter:
    @staticmethod
    def bin_to_toml(bin_bytes: bytes) -> str:
        if not bin_bytes.startswith(b"CAFF"):
            raise ValueError("Invalid format: missing CAFF header.")

        lsbl_idx = bin_bytes.find(b"LSBL")
        if lsbl_idx == -1:
            raise ValueError("Invalid file: missing LSBL block.")

        # Read number of strings in block
        string_count = struct.unpack("<I", bin_bytes[lsbl_idx + 32 : lsbl_idx + 36])[0]

        # 1. Locate all UTF-16LE dialogue strings following LSBL
        str_pattern = re.compile(b'(?:[\x20-\x7E]\x00){2,}')
        dialogue_strings = []
        scan_offset = lsbl_idx + 48
        
        for match in str_pattern.finditer(bin_bytes[scan_offset:]):
            start = scan_offset + match.start()
            end = scan_offset + match.end()
            raw_bytes = bin_bytes[start:end]
            decoded = raw_bytes.decode("utf-16le", errors="ignore")
            
            # Filter out key names
            if not decoded.startswith("cutscene_") and not decoded == "EmptyString":
                dialogue_strings.append((start, end - start, decoded))
            
            if len(dialogue_strings) == string_count:
                break

        # 2. Locate ASCII key names
        keys = []
        ascii_region = bin_bytes[scan_offset:]
        key_matches = re.findall(b'(?:cutscene_[A-Za-z0-9_]+|EmptyString)', ascii_region)
        
        for k in key_matches:
            decoded_key = k.decode("ascii")
            if decoded_key not in keys:
                keys.append(decoded_key)
            if len(keys) == string_count:
                break

        while len(keys) < len(dialogue_strings):
            keys.append(f"string_key_{len(keys)}")

        # 3. Extract Build Path & Script metadata
        remaining = bin_bytes[scan_offset:]
        audio_meta = ""
        audio_start = remaining.find(b";")
        if audio_start != -1:
            audio_end = remaining.find(b"\x00", audio_start)
            if audio_end != -1:
                audio_meta = remaining[audio_start:audio_end].decode("ascii", errors="ignore")

        build_path = ""
        path_start = remaining.find(b":\\")
        if path_start != -1:
            path_start_offset = path_start - 1
            path_end = remaining.find(b"\x00", path_start_offset)
            if path_end != -1:
                build_path = remaining[path_start_offset:path_end].decode("ascii", errors="ignore")

        # Construct TOML
        toml_lines = [
            f"[meta]",
            f"build_path = {json.dumps(build_path)}",
            "",
            f"[script]",
            f"audio_meta = {json.dumps(audio_meta)}",
            ""
        ]

        for i, (_, _, text_val) in enumerate(dialogue_strings):
            key_val = keys[i] if i < len(keys) else f"key_{i}"
            toml_lines.append("[[entries]]")
            toml_lines.append(f"key = {json.dumps(key_val)}")
            toml_lines.append(f"text = {json.dumps(text_val)}")
            toml_lines.append("")

        toml_lines.append("[binary]")
        toml_lines.append(f'template_hex = "{bin_bytes.hex()}"\n')

        return "\n".join(toml_lines)

    @staticmethod
    def toml_to_bin(toml_str: str) -> bytes:
        parsed = tomllib.loads(toml_str)
        template_hex = parsed.get("binary", {}).get("template_hex", "")
        
        if not template_hex:
            raise ValueError("TOML file missing [binary] template_hex field.")

        raw_data = bytearray(bytes.fromhex(template_hex))
        entries = parsed.get("entries", [])

        lsbl_idx = raw_data.find(b"LSBL")
        if lsbl_idx == -1:
            raise ValueError("Invalid template binary: missing LSBL block.")

        str_pattern = re.compile(b'(?:[\x20-\x7E]\x00){2,}')
        scan_offset = lsbl_idx + 48
        
        matches = []
        for match in str_pattern.finditer(raw_data[scan_offset:]):
            start = scan_offset + match.start()
            end = scan_offset + match.end()
            raw_bytes = raw_data[start:end]
            decoded = raw_bytes.decode("utf-16le", errors="ignore")
            
            if not decoded.startswith("cutscene_") and not decoded == "EmptyString":
                matches.append((start, end - start))
            
            if len(matches) == len(entries):
                break

        # Process replacement in reverse order to preserve offsets
        for i in reversed(range(min(len(entries), len(matches)))):
            start_off, old_byte_len = matches[i]
            new_text = entries[i].get("text", "")
            new_encoded = new_text.encode("utf-16le")

            if len(new_encoded) == old_byte_len:
                raw_data[start_off : start_off + old_byte_len] = new_encoded
            else:
                raw_data[start_off : start_off + old_byte_len] = new_encoded
                
                if len(entries) == 1:
                    char_count_offset = start_off - 4
                    new_char_count = len(new_text) + 1
                    struct.pack_into("<I", raw_data, char_count_offset, new_char_count)

        return bytes(raw_data)

    @staticmethod
    def verify_lossless(original_bytes: bytes, toml_str: str) -> tuple[bool, str]:
        """In-memory roundtrip validation test."""
        repacked_bytes = CaffTomlConverter.toml_to_bin(toml_str)
        
        if original_bytes == repacked_bytes:
            return True, "100% byte-for-byte match"

        # Locate first byte mismatch for diagnostics
        min_len = min(len(original_bytes), len(repacked_bytes))
        diff_offset = next((i for i in range(min_len) if original_bytes[i] != repacked_bytes[i]), min_len)
        
        return False, f"Mismatch detected at offset 0x{diff_offset:X} (Original: {len(original_bytes)} bytes, Repacked: {len(repacked_bytes)} bytes)"


# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage:")
        print("  Unpack: python caff_tool.py unpack input.bin output.toml")
        print("  Pack:   python caff_tool.py pack input.toml output.bin")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "unpack":
        in_bin_path = sys.argv[2]
        out_toml_path = sys.argv[3]

        with open(in_bin_path, "rb") as f:
            original_data = f.read()

        # 1. Generate TOML in memory
        generated_toml = CaffTomlConverter.bin_to_toml(original_data)

        # 2. In-memory roundtrip check
        is_lossless, status_msg = CaffTomlConverter.verify_lossless(original_data, generated_toml)
        if not is_lossless:
            print(f"[ERROR] Lossless verification failed for '{in_bin_path}'!")
            print(f"        Details: {status_msg}")
            sys.exit(1)

        # 3. Write TOML to disk only after verification passes
        with open(out_toml_path, "w", encoding="utf-8") as f:
            f.write(generated_toml)

        print(f"[SUCCESS] Verified ({status_msg}) & Exported {in_bin_path} -> {out_toml_path}")

    elif mode == "pack":
        in_toml_path = sys.argv[2]
        out_bin_path = sys.argv[3]

        with open(in_toml_path, "r", encoding="utf-8") as f:
            toml_content = f.read()

        modded_bin = CaffTomlConverter.toml_to_bin(toml_content)
        
        with open(out_bin_path, "wb") as f:
            f.write(modded_bin)

        print(f"[SUCCESS] Repacked {in_toml_path} -> {out_bin_path}")