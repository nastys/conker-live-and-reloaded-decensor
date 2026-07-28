# Conker: Live &amp; Reloaded - Decensor Patch/Mod

A lot of work and research has yet to be done, including proper reverse-engineering the CAFF version used by the game (for the scripts), decensoring them, synthesizing the missing (beeped) audio (using the official uncensored audio where possible), repacking the audio files.

UPDATE - by Vaani: uncensored every text script in the *SINGLE PLAYER* game (that I could find. May have missed some)

Decensored text so far:
- Every script in English (by Vaani)
- Every script in Italian (by nastys)
- Every script in French (by nastys)
- Every script in Spanish (by Theconker64)

## Downloading and installing the decensored audio files

After cloning the repository, run "decompress_voicebanks.bat" (Windows 10/11) or "decompress_voicebanks.sh" (Linux/macOS) before copying the files. See the [wiki](https://github.com/nastys/conker-live-and-reloaded-decensor/wiki) for further instructions for your platform.

NOTE: Make sure to delete any cached files in your Xbox's X:\ partition; otherwise, you will not hear the decensored audio.

Decensored audio so far:
- The Great Mighty Poo song

## Editing

### CAFF text files ("default.bin")

You can use a hex editor, the legacy [CAFFTextEditor](https://github.com/nastys/CAFFTextEditor/releases), or the experimental, vibe-coded caff_tool.py provided in this repo (if you need batch processing).

### XWB voicebanks

Some useful tools:
http://aluigi.altervista.org/papers/unxwb.zip
https://archive.org/details/xbox-sdks (version 5849)

If you are working on a specific file, do not run "decompress_voicebanks" (to avoid recompressing everything later with "compress_voicebanks"), and only commit the *.xwb.zip file you have modified.
