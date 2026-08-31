from dataclasses import dataclass
from struct import pack, unpack
from typing import Self


@dataclass
class TengokuGlyph:
	pixels: list[list[bool]]
	spacing: int

	@classmethod
	def load(cls, font_file: str, spacing_file: str, glyph_size: int) -> list[Self]:
		glyphs: list[cls] = []

		if glyph_size % 8 != 0:
			raise ValueError('glyph size must be multiple of 8')

		glyph_width: int = 16
		glyph_sections: int = glyph_size // 8

		with open(font_file, 'rb') as fp:
			font_data: bytes = fp.read()

		with open(spacing_file, 'rb') as fp:
			spacing_data: bytes = fp.read()

		if len(font_data) % glyph_size != 0:
			raise ValueError('font file size must be multiple of glyph size')

		num_glyphs: int = len(font_data) // glyph_size

		if len(spacing_data) < num_glyphs:
			raise ValueError('spacing file contains less glyphs than font file')

		for i in range(num_glyphs):
			data_idx: int = i * glyph_size
			glyph_qwords: list[int] = list(
				unpack(f'<{'Q' * glyph_sections}', font_data[data_idx:data_idx + glyph_size])
			)

			glyph_data: list[list[bool]] = []

			for qword in glyph_qwords:
				bit_planes: list[int] = [
					(qword >> shift) & 0x1111111111111111
					for shift in range(4)
				]

				row_data: list[bool] = []
				for nibbles in bit_planes:
					for pixel in [(nibbles >> (bit * 4)) & 1 for bit in range(glyph_width)]:
						row_data.append(bool(pixel))
					glyph_data.append(row_data.copy())
					row_data.clear()

			glyph_spacing: int = spacing_data[i]

			glyphs.append(cls(glyph_data, glyph_spacing))

		return glyphs

	@staticmethod
	def save(glyphs: list[TengokuGlyph], font_file: str, spacing_file: str) -> None:
		glyph_width: int = 16
		try:
			glyph_height: int = len(glyphs[0].pixels)
		except IndexError:
			raise ValueError('invalid glyph data at index 0')

		if glyph_height % 4 != 0:
			raise ValueError('glyph height must be multiple of 4')

		for i, glyph in enumerate(glyphs):
			if len(glyph.pixels) != glyph_height:
				raise ValueError(f'mismatching glyph height at index {i} ({len(glyph.pixels)} != {glyph_height})')

			for row in glyph.pixels:
				if len(row) != glyph_width:
					raise ValueError(f'invalid glyph width at index {i} ({len(row)} != {glyph_width})')

		with open(font_file, 'wb') as fp:
			for glyph in glyphs:
				for section_idx in range(0, len(glyph.pixels), 4):
					rows: list[list[bool]] = glyph.pixels[section_idx:section_idx + 4]

					qword: int = 0
					for row_idx, row in enumerate(rows):
						for pixel_idx, pixel in enumerate(row):
							if pixel:
								qword |= 1 << (pixel_idx * 4 + row_idx)

					fp.write(pack('<Q', qword))

		with open(spacing_file, 'wb') as fp:
			for glyph in glyphs:
				fp.write(pack('<B', glyph.spacing))


def main() -> None:
	glyphs: list[TengokuGlyph] = TengokuGlyph.load(
		'files/text_small_glyphs.bin',
		'files/text_small_glyph_sizes.bin',
		0x18
	)

	for glyph in glyphs:
		print(glyph.spacing)


if __name__ == '__main__':
	main()
