# 8x8 BG text (menus, shops, item/monster data, Mobile Adapter messages)

- Font: 512 raw 4bpp tiles at ROM 0x0BEDF0 (uncompressed), loaded to BG char block 1 (VRAM 0x4000). Tile index ==
  code == name-entry grid index (`tbl/jp8.tbl`, generated from the grid table 0x0CFB82). Latin A-Z/a-z, digits
  exist as 8 px fixed-width tiles.
- Codes: u16. < 0x1FF glyph tile; 0x1FF newline; 0x200+n palette n for following glyphs; 0 end.
- Strings are mostly packed WITHOUT terminators; the code passes lengths as Thumb immediates, e.g.
  0x08046A12 `ldr r1,=0x080BDE22; adds r0,r7; movs r2,#9; bl 0x080365DC` (strncpy16: copy until 0 or max).
  Shop dialogue (0x0A7FF6-) is 0-terminated with 0x1FF line breaks; item descriptions (0x0B720C-) packed.
- Messages are composed into a RAM buffer (e.g. 0x03000CE2) and drawn by the renderer at ~0x0803D300:
  map entry = [0x03001D72] + code | [0x03001D74] (palette), one line at a time, DMA to the BG map; caller gives
  max width/lines.
- 40 call sites of strncpy16 (0x080365DC): `disasm.py xref rom 080365DC`.

## Regions (pointer-referenced; work/dump8.py writes decoded copies with pointer marks)
| range | content |
|---|---|
| 0x09DB34-0x0A1108 | Mobile Adapter / communication messages (~5300 kana) |
| 0x0A12A8-0x0A1A40 | training / event messages |
| 0x0A7FF6-0x0A9764 | shop dialogue (0-terminated) |
| 0x0AEE14-0x0B6AF0 | monster/item data records with embedded names |
| 0x0B720C-0x0B78D0 | item descriptions |
| 0x0BCC2C-0x0BEDC4 | name-entry kana grid, menu labels, menu messages |
| 0x0C5884-0x0C6DF0 | stage names, map labels |

## Plan
Fixed-width English with a restyled Latin font; relocate strings and patch pointer literals + length immediates
per call site; pre-rendered proportional label tiles (in freed kana/kanji tile codes) where a label cannot fit.
