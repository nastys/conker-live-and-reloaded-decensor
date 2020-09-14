# Conker: Live &amp; Reloaded - Decensor Patch/Mod

A lot of work and research has yet to be done, including proper reverse-engineering the CAFF version used by the game (for the scripts), decensoring them, synthesizing the missing (beeped) audio (using the official uncensored audio where possible), repacking the audio files.

For now, only a few decensored English scripts are included, as a proof of concept. These were manually decensored with a hex editor.

UPDATE: string editor: https://github.com/nastys/CAFFTextEditor/releases


## Downloading and installing decensored audio files

NOTE: Make sure to delete any cached files in your Xbox's X:\ partition; otherwise, you will not hear the decensored audio.

To properly download the audio files, you MUST install Git LFS: https://git-lfs.github.com/
Then clone this repository with ``git lfs clone``.

DO NOT DOWNLOAD THE "CODE" DIRECTLY (i.e. as a .zip file)
