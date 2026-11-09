from tengoku import TengokuGlyph
from tkinter import Tk, Menu, Canvas, Event, StringVar, IntVar, filedialog, simpledialog
from tkinter.ttk import (
	PanedWindow,
	Frame,
	Treeview,
	Label,
	Entry,
	Style,
	Scrollbar,
	Spinbox
)
import math


class FontEditor(Tk):
	def __init__(self) -> None:
		super().__init__()

		self.glyphs: dict[str, TengokuGlyph] = {}

		# main window init
		self.title('Tengoku Font Editor')
		self.geometry('900x600')

		self.update_idletasks()

		width: int = self.winfo_width()
		height: int = self.winfo_height()

		center_x: int = (self.winfo_screenwidth() - width) // 2
		center_y: int = (self.winfo_screenheight() - height) // 2

		self.geometry(f'{width}x{height}+{center_x}+{center_y}')

		self.minsize(500, 300)

		menu_bar: Menu = Menu(self)
		self.config(menu=menu_bar)

		file_menu: Menu = Menu(menu_bar, tearoff=False)
		menu_bar.add_cascade(label='File', menu=file_menu)

		accelerator_key: str = (
			'Cmd' if self.tk.call('tk', 'windowingsystem') == 'aqua'
			else 'Ctrl'
		)

		file_menu.add_command(
			label='Import Glyphs',
			command=self.import_glyphs,
			accelerator=f'{accelerator_key}+I'
		)

		self.bind('<Control-i>', self.import_glyphs)
		self.bind('<Command-i>', self.import_glyphs)

		file_menu.add_command(
			label='Export Glyphs',
			command=self.export_glyphs,
			accelerator=f'{accelerator_key}+E'
		)

		self.bind('<Control-e>', self.export_glyphs)
		self.bind('<Command-e>', self.export_glyphs)

		self.pane: PanedWindow = PanedWindow(self, orient='horizontal')
		self.pane.pack(fill='both', expand=True)

		self.left: Frame = Frame(self.pane)
		self.pane.add(self.left, weight=1)

		self.right: Frame = Frame(self.pane)
		self.pane.add(self.right, weight=50)

		# codepoint list init
		base_frame: Frame = Frame(self.left)
		base_frame.pack(side='top', fill='x', padx=5, pady=5)

		Label(
			base_frame,
			text='Base codepoint:'
		).pack(side='left')

		self.base_codepoint: StringVar = StringVar(value='0000')

		validate_cmd: tuple[str, str] = (self.register(self.validate_codepoint), '%P')

		base_codepoint_entry: Entry = Entry(
			base_frame,
			textvariable=self.base_codepoint,
			width=10,
			validate='key',
			validatecommand=validate_cmd
		)
		base_codepoint_entry.pack(side='left', padx=(5, 0))
		base_codepoint_entry.bind('<FocusOut>', self.update_codepoints)

		style: Style = Style(self)
		style.configure(
			'Codepoint.Treeview',
			font=('TkDefaultFont', 12),
			rowheight=20
		)

		tree_frame: Frame = Frame(self.left)
		tree_frame.pack(
			side='top',
			fill='both',
			expand=True
		)

		self.codepoint_tree: Treeview = Treeview(
			tree_frame,
			columns=('codepoint',),
			show='',
			selectmode='browse',
			style='Codepoint.Treeview'
		)

		self.codepoint_tree.column(
			'codepoint',
			width=100,
			stretch=True
		)

		scrollbar: Scrollbar = Scrollbar(
			tree_frame,
			orient='vertical',
			command=self.codepoint_tree.yview
		)

		self.codepoint_tree.configure(
			yscrollcommand=scrollbar.set
		)

		self.codepoint_tree.pack(
			side='left',
			fill='both',
			expand=True
		)

		scrollbar.pack(
			side='right',
			fill='y'
		)

		self.codepoint_tree.bind(
			'<<TreeviewSelect>>',
			self.codepoint_selected
		)

		# editor init
		self.glyph: TengokuGlyph | None = None

		self.glyph_canvas: Canvas = Canvas(
			self.right,
			background='gray',
			highlightthickness=0
		)
		self.glyph_canvas.pack(
			side='top',
			fill='both',
			expand=True
		)

		self.glyph_canvas_padding: int = 20

		self.drag_value: bool | None = None
		self.last_drag_pixel: tuple[int, int] | None = None

		bottom_frame: Frame = Frame(self.right)
		bottom_frame.pack(
			side='bottom',
			fill='x',
			padx=5,
			pady=5
		)

		Label(
			bottom_frame,
			text='Glyph spacing:'
		).pack(side='left')

		self.glyph_spacing_var: IntVar = IntVar(value=0)
		self.glyph_spacing_var.trace_add('write', self.glyph_spacing_changed)

		Spinbox(
			bottom_frame,
			from_=0,
			to=16,
			textvariable=self.glyph_spacing_var,
			width=5
		).pack(
			side='left',
			padx=(5, 0)
		)

		self.glyph_canvas.bind('<Configure>', self.draw_glyph)
		self.glyph_canvas.bind('<Button-1>', self.pixel_click)
		self.glyph_canvas.bind('<B1-Motion>', self.pixel_drag)
		self.glyph_canvas.bind('<ButtonRelease-1>', self.pixel_release)

	@property
	def glyph_width(self) -> int:
		if self.glyph is None:
			return 0

		return min([len(row) for row in self.glyph.pixels])

	@property
	def glyph_height(self) -> int:
		if self.glyph is None:
			return 0

		return len(self.glyph.pixels)

	def import_glyphs(self, *_) -> None:
		glyph_filename: str | None = filedialog.askopenfilename(
        	title='Import Glyph File',
    	    filetypes=[
    	        ('Glyph files', '*.bin'),
    	        ('All files', '*.*')
    	    ]
    	)

		glyph_spacing_filename: str | None = filedialog.askopenfilename(
        	title='Import Glyph Spacing File',
    	    filetypes=[
    	        ('Glyph spacing files', '*.bin'),
    	        ('All files', '*.*')
    	    ]
    	)

		glyph_size: int | None = simpledialog.askinteger(
			'Glyph Size',
			'Enter glyph size (in bytes):',
			initialvalue=0x18,
			minvalue=1
		)

		if not glyph_filename or not glyph_spacing_filename or not glyph_size:
			return

		imported_glyphs: list[TengokuGlyph] = TengokuGlyph.load(
			glyph_filename,
			glyph_spacing_filename,
			glyph_size
		)

		self.glyphs = {}
		self.codepoint_tree.delete(*self.codepoint_tree.get_children())

		for i, glyph in enumerate(imported_glyphs):
			item: str = self.codepoint_tree.insert(
				'',
				i,
				values=('',)
			)

			self.glyphs[item] = glyph

		self.update_codepoints()

	def export_glyphs(self, *_) -> None:
		glyph_filename: str | None = filedialog.asksaveasfilename(
			title='Export Glyph File',
			filetypes=[
				('Glyph files', '*.bin'),
				('All files', '*.*')
			]
		)

		glyph_spacing_filename: str | None = filedialog.asksaveasfilename(
			title='Export Glyph Spacing File',
			filetypes=[
				('Glyph spacing files', '*.bin'),
				('All files', '*.*')
			]
		)

		if not glyph_filename or not glyph_spacing_filename:
			return

		TengokuGlyph.save(list(self.glyphs.values()), glyph_filename, glyph_spacing_filename)

	@staticmethod
	def validate_codepoint(value: str) -> bool:
		if len(value) > 4:
			return False

		if value == '':
			return True

		return all(c in '0123456789ABCDEFabcdef' for c in value)

	def codepoint_selected(self, _) -> None:
		selection: tuple[str, ...] = self.codepoint_tree.selection()

		if not selection:
			return

		item: str = selection[0]
		self.glyph = self.glyphs[item]
		self.glyph_spacing_var.set(self.glyph.spacing)

	def update_codepoints(self, *_) -> None:
		base_codepoint: int = int(self.base_codepoint.get(), 16)
		self.base_codepoint.set(format(base_codepoint, '04X').upper())

		for i, item in enumerate(self.codepoint_tree.get_children()):
			codepoint: int = base_codepoint + i

			char: str
			try:
				char = chr(codepoint)
				char.encode('utf-8', errors='strict')
			except UnicodeError:
				char = ''

			self.codepoint_tree.item(
				item,
				values=(f'U+{codepoint:04X} {char}',)
			)

	def glyph_spacing_changed(self, *_) -> None:
		if self.glyph is not None:
			self.glyph.spacing = self.glyph_spacing_var.get()

		self.draw_glyph()

	def draw_glyph(self, *_):
		if self.glyph is None:
			return

		canvas_width: int = self.glyph_canvas.winfo_width()
		canvas_height: int = self.glyph_canvas.winfo_height()

		scale: float = min(
			(canvas_width - self.glyph_canvas_padding * 2) / self.glyph_width,
			(canvas_height - self.glyph_canvas_padding * 2) / self.glyph_height
		)

		base_x: float = (canvas_width - self.glyph_width * scale) / 2
		base_y: float = (canvas_height - self.glyph_height * scale) / 2

		self.glyph_canvas.delete('glyph')

		for y in range(self.glyph_height):
			for x in range(self.glyph_width):
				left: float = base_x + x * scale
				top: float = base_y + y * scale
				right: float = base_x + (x + 1) * scale
				bottom: float = base_y + (y + 1) * scale

				self.glyph_canvas.create_rectangle(
					left, top, right, bottom,
					fill='black' if self.glyph.pixels[y][x] else 'white',
					outline='gray',
					tags='glyph'
				)

		glyph_spacing: int = self.glyph.spacing

		spacing_line_x: float = base_x + (glyph_spacing * scale) + 5
		spacing_line_y: float = base_y + (self.glyph_height * scale) + 7

		self.glyph_canvas.create_line(
			base_x - 5,
			spacing_line_y,
			spacing_line_x,
			spacing_line_y,
			fill='red',
			width=1,
			tags='glyph'
		)

		self.glyph_canvas.create_line(
			base_x - 5,
			spacing_line_y - 5,
			base_x - 5,
			spacing_line_y + 5,
			fill='red',
			width=1,
			tags='glyph'
		)

		self.glyph_canvas.create_line(
			spacing_line_x,
			spacing_line_y - 5,
			spacing_line_x,
			spacing_line_y + 5,
			fill='red',
			width=1,
			tags='glyph'
		)

	def get_pixel_at(self, mouse_x: float, mouse_y: float) -> tuple[int, int] | None:
		if self.glyph is None:
			return None

		canvas_width: int = self.glyph_canvas.winfo_width()
		canvas_height: int = self.glyph_canvas.winfo_height()

		scale: float = min(
			(canvas_width - self.glyph_canvas_padding * 2) / self.glyph_width,
			(canvas_height - self.glyph_canvas_padding * 2) / self.glyph_height
		)

		base_x: float = (canvas_width - self.glyph_width * scale) / 2
		base_y: float = (canvas_height - self.glyph_height * scale) / 2

		x: int = math.floor((mouse_x - base_x) / scale)
		y: int = math.floor((mouse_y - base_y) / scale)

		if not (0 <= x < self.glyph_width and 0 <= y < self.glyph_height):
			return None

		return x, y

	def pixel_click(self, event: Event) -> None:
		self.glyph_canvas.focus_set()

		pixel: tuple[int, int] | None = self.get_pixel_at(event.x, event.y)

		if pixel is None:
			return

		x: int; y: int
		x, y = pixel

		self.drag_value = not self.glyph.pixels[y][x]
		self.last_drag_pixel = pixel
		self.glyph.pixels[y][x] = self.drag_value

		self.draw_glyph(None)

	def pixel_drag(self, event: Event) -> None:
		pixel: tuple[int, int] | None = self.get_pixel_at(event.x, event.y)

		if pixel is None or pixel == self.last_drag_pixel:
			return

		x: int; y: int
		x, y = pixel

		self.glyph.pixels[y][x] = self.drag_value
		self.last_drag_pixel = pixel

		self.draw_glyph(None)

	def pixel_release(self, _):
		self.drag_value = None
		self.last_drag_pixel = None
