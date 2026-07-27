import sys
import struct
import json

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

        # 1. Extract UTF-16 Key preceding LSBL block
        key_bytes = bin_bytes[lsbl_idx - 42 : lsbl_idx - 2]
        key = key_bytes.decode("utf-16le", errors="ignore").rstrip("\x00")

        # 2. Extract Dialogue String
        char_count_offset = lsbl_idx + 44
        char_count = struct.unpack("<I", bin_bytes[char_count_offset:char_count_offset + 4])[0]
        text_start = lsbl_idx + 48
        text_byte_len = (char_count - 1) * 2  # Exclude null terminator
        dialogue_text = bin_bytes[text_start : text_start + text_byte_len].decode("utf-16le")

        # 3. Extract Audio Metadata & Build Path
        remaining = bin_bytes[text_start + text_byte_len + 2 :]
        
        audio_meta = ""
        audio_start = remaining.find(b";")
        if audio_start != -1:
            audio_end = remaining.find(b"\x00", audio_start)
            audio_meta = remaining[audio_start:audio_end].decode("ascii", errors="ignore")

        build_path = ""
        path_start = remaining.find(b":\\")
        if path_start != -1:
            path_start_offset = path_start - 1
            path_end = remaining.find(b"\x00", path_start_offset)
            build_path = remaining[path_start_offset:path_end].decode("ascii", errors="ignore")

        # Embed original binary as hex
        template_hex = bin_bytes.hex()

        return f"""[meta]
key = {json.dumps(key)}
build_path = {json.dumps(build_path)}

[script]
audio_meta = {json.dumps(audio_meta)}

[dialogue]
text = {json.dumps(dialogue_text)}

[binary]
template_hex = "{template_hex}"
"""

    @staticmethod
    def toml_to_bin(toml_str: str) -> bytes:
        parsed = tomllib.loads(toml_str)
        new_text = parsed.get("dialogue", {}).get("text", "")
        template_hex = parsed.get("binary", {}).get("template_hex", "")
        
        if not template_hex:
            raise ValueError("TOML file missing [binary] template_hex field.")

        raw_data = bytearray(bytes.fromhex(template_hex))

        lsbl_idx = raw_data.find(b"LSBL")
        if lsbl_idx == -1:
            raise ValueError("Invalid template binary inside TOML: missing LSBL block.")

        char_count_offset = lsbl_idx + 44
        old_char_count = struct.unpack("<I", raw_data[char_count_offset:char_count_offset + 4])[0]
        old_text_byte_len = old_char_count * 2  # Including null terminator

        # Build new text payload
        new_encoded = new_text.encode("utf-16le") + b"\x00\x00"
        new_char_count = len(new_text) + 1

        # Update char count prefix
        struct.pack_into("<I", raw_data, char_count_offset, new_char_count)

        # Update block payload length field
        payload_len_offset = lsbl_idx + 16
        old_payload_len = struct.unpack("<I", raw_data[payload_len_offset:payload_len_offset + 4])[0]
        length_diff = len(new_encoded) - old_text_byte_len
        struct.pack_into("<I", raw_data, payload_len_offset, old_payload_len + length_diff)

        # Splice new text bytes into binary data
        text_start = lsbl_idx + 48
        raw_data[text_start : text_start + old_text_byte_len] = new_encoded

        return bytes(raw_data)


# --- Command-Line Interface ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage:")
        print("  Unpack: python caff_tool.py unpack input.bin output.toml")
        print("  Pack:   python caff_tool.py pack input.toml output.bin")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "unpack":
        with open(sys.argv[2], "rb") as f:
            data = f.read()
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            f.write(CaffTomlConverter.bin_to_toml(data))
        print(f"[SUCCESS] Exported {sys.argv[2]} -> {sys.argv[3]}")

    elif mode == "pack":
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            toml_content = f.read()

        modded_bin = CaffTomlConverter.toml_to_bin(toml_content)
        
        with open(sys.argv[3], "wb") as f:
            f.write(modded_bin)
        print(f"[SUCCESS] Repacked {sys.argv[2]} -> {sys.argv[3]}")