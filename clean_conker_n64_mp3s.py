import re
import sys
from pathlib import Path

# 1. Audiokinetica lip-sync pattern
# https://www.audiokinetic.com/en/community/blog/video-game-sound-archiving-part-2/
LIPSYNC_PATTERN = re.compile(
    rb"\x4C\x3A\x01.\x80[\x80\x81]..\x00", flags=re.DOTALL
)

# MP3 Bitrate Lookup Tables (kbps)
BITRATES_MPEG1 = [
    0,
    32,
    40,
    48,
    56,
    64,
    80,
    96,
    112,
    128,
    160,
    192,
    224,
    256,
    320,
    0,
]
BITRATES_MPEG2 = [
    0,
    8,
    16,
    24,
    32,
    40,
    48,
    56,
    64,
    80,
    96,
    112,
    128,
    144,
    160,
    0,
]
SAMPLERATES = {
    3: [44100, 48000, 32000, 0],
    2: [22050, 24000, 16000, 0],
    0: [11025, 12000, 8000, 0],
}


def get_frame_length(header: bytes):
    """Calculates standard MP3 frame length in bytes, or returns None if invalid header."""
    if len(header) < 4 or header[0] != 0xFF or (header[1] & 0xE0) != 0xE0:
        return None

    ver = (header[1] >> 3) & 0x03
    layer = (header[1] >> 1) & 0x03
    if layer != 1 or ver == 1:
        return None

    bitrate_idx = (header[2] >> 4) & 0x0F
    sr_idx = (header[2] >> 2) & 0x03
    padding = (header[2] >> 1) & 0x01

    if bitrate_idx in (0, 15) or sr_idx == 3:
        return None

    if ver == 3:  # MPEG 1
        bitrate = BITRATES_MPEG1[bitrate_idx] * 1000
        sr = SAMPLERATES[3][sr_idx]
        return int(144 * bitrate / sr) + padding
    else:  # MPEG 2 / 2.5
        bitrate = BITRATES_MPEG2[bitrate_idx] * 1000
        sr = SAMPLERATES.get(ver, [0, 0, 0, 0])[sr_idx]
        if sr == 0:
            return None
        return int(72 * bitrate / sr) + padding


def sanitize_mp3_frames(raw_data: bytes) -> bytes:
    """Walks the stream and keeps ONLY complete, valid MP3 frames, discarding trailing garbage."""
    clean_stream = bytearray()
    idx = 0
    total_len = len(raw_data)

    while idx < total_len - 4:
        frame_len = get_frame_length(raw_data[idx : idx + 4])

        # Ensure the entire frame exists in the buffer
        if frame_len and (idx + frame_len <= total_len):
            clean_stream.extend(raw_data[idx : idx + frame_len])
            idx += frame_len
        else:
            # Skip non-frame garbage / trailing padding bytes
            idx += 1

    return bytes(clean_stream)


def process_conker_audio(input_path: Path, output_path: Path):
    try:
        with open(input_path, "rb") as f:
            data = f.read()
    except IOError as e:
        print(f"Error reading {input_path.name}: {e}")
        return

    # Step 1: Strip 9-byte lip-sync animation blocks
    stripped_data, count = LIPSYNC_PATTERN.subn(b"", data)

    # Step 2: Sanitize frame boundaries and discard trailing padding junk
    final_clean_data = sanitize_mp3_frames(stripped_data)

    try:
        with open(output_path, "wb") as f_out:
            f_out.write(final_clean_data)
        print(
            f"[{input_path.name}] Success! Removed {count} lip-sync blocks & trimmed line-end padding -> {output_path.name}"
        )
    except IOError as e:
        print(f"Error writing {output_path.name}: {e}")


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    if target.is_file():
        out_name = target.stem + "_perfect" + target.suffix
        process_conker_audio(target, target.parent / out_name)
    else:
        out_dir = target / "cleaned_output"
        out_dir.mkdir(exist_ok=True)
        files = [
            f
            for f in target.iterdir()
            if f.suffix.lower() in [".mp3", ".bin", ".dat", ".raw"]
            and not f.name.endswith("_perfect.mp3")
        ]
        for f in files:
            process_conker_audio(f, out_dir / f"{f.stem}_perfect.mp3")


if __name__ == "__main__":
    main()