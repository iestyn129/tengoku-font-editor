#!/usr/bin/env python3

from gui import FontEditor
from sys import argv


def main() -> None:
	app: FontEditor = FontEditor()

	if len(argv) > 3:
		app.import_glyphs(
			glyph_filename=argv[2],
			glyph_spacing_filename=argv[3],
			glyph_size=int(argv[4], base=0x10)
		)

	app.mainloop()


if __name__ == '__main__':
	main()
