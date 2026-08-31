# Tengoku Font Editor
An experimental little program for editing fonts from Rhythm Tengoku.
It's intended to be used with fonts split into UTF-8 blocks, as seen in [Rhythm Heaven Advance](https://github.com/RHAdvance/RhythmHeavenAdvance/tree/utf-8).

## Requirements
- Python 3.14 or later

## How To Use
You can simply run `main.py` with Python 3.14 or later to launch the program.

You can import a font by going to `File -> Import Glyphs`, or by pressing `Cmd/Ctrl + I`.
To import a font you need to select the `.bin` file containing the actual glyphs,
the `.bin` file containing the spacings for the glyphs, as well as the size of each glyph
(this is 24 for the small and medium font, and 32 for the large font).

Exporting is much the same, select `File -> Export Glyphs`, or press `Cmd/Ctrl + E`,
and choose the files you wish export the glyphs and their spacings to.
The glyph size is automatically calculated when exporting.

## Known Issues
- There is no undo/redo.
- Errors are only printed to the console.
- You cannot create new glyphs in the editor, only edit existing ones.
