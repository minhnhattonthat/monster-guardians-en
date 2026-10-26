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
| 0x0A12A8-0x0A1A38 | training / event messages (0x0A1A38 = port map tile set header, not text: issue #1) |
| 0x0A7FF6-0x0A9764 | shop dialogue (0-terminated) |
| 0x0AEE14-0x0B6AF0 | monster/item data records with embedded names |
| 0x0B720C-0x0B78D0 | item descriptions |
| 0x0BCC2C-0x0BEDC4 | name-entry kana grid, menu labels, menu messages |
| 0x0C5884-0x0C6DF0 | stage names, map labels |

## Engine (built 2026-10-14; user chose engine work over abbreviations)
- Text is stored in place. English uses the normal 8 px Latin tiles when it fits the JP slot, else **pair codes**
  `0x4000 + (a-0x20)*0x60 + (b-0x20)` (two condensed 3 px letters per tile; 0x200+ and 0x2000-0x200F are
  palette codes in some drawers). Encoder: `tools/menu8.py encode_en`; art `font/cond8.txt`.
- `asm/menu8.asm` (armips, run by `tools/insert.py assemble`): hooks at every code->tile site call `conv`, which
  keeps an LRU cache (RAM 0x0203F000, free in all sampled screens) of pair codes in free font slots (kana/kanji
  codes, `build/pool.bin`) of the font copy in VRAM. The font copy is found by a signature tile (code 0x0C) at the
  char base of BG3..BG0, else by scanning; stale copies (map keeps the menu's under its picture) are skipped.
  Every hit re-verifies the 32-byte tile, so font reloads are healed automatically. One code = one tile, so all
  layout code is unchanged. Code lives in the zero gap 0x0809C400-0x0809C8C0 (bl range); the 96x96 pair table
  (296 KB) at 0x087A0000.
- Hooked sites: 0x08027E1C/F58/FC0/803C (0-terminated drawers), 0x08027EE8 (typewriter: shop dialogue, code |
  0xF000), 0x0803D178/1F6 (line drawer), 0x0803D306/31A/3B2/3C6
  (renderer + palette tests), 0x080625D0/0x08062666 (char animator: fusion result labels),
  0x0807CBA4 (window module: world map), sprite tile copies 0x0801C788/0801F6B2/
  0807EBD2/08082B0C/08064BDC. New garbage on a screen = an unhooked drawer: find its map write (watch.lua on the BG
  map row), add a stub.
- Name fields: `tools/records.py` replaces every zero-padded 8-code name field in 0x0AE000-0x0B6B00 (463 fields).
- Default names: Leo relocated (+patches 0x0492C4, 0x049314, 0x057734, 0x057E1A, DMA counts 0x055120/0x05539C),
  Tina in place; both normal tiles because `{name}` maps grid codes into the story font.
- Strings passed to strncpy16 (0x080365DC) are padded with 0 so composed messages have no gaps; others with spaces.

## Plan (decided 2026-10-14)
Per-site relocation is fragile: packed strings are often reached by base+offset arithmetic, lengths are Thumb
immediates spread over ~750 code sites (work/sites8.py, work/lencov.py). So:
- **In place by default**: English must fit the JP code count. Normal text uses the 8 px Latin tiles (restyled).
- **Condensed digraph tiles** (two 3-4 px letters per tile, in the freed kana/kanji codes 0x40-0xDF, 0x170-0x193)
  only where the English does not fit; chosen globally by an encoder. Monster/item names live in fixed 8-code
  record fields (also the rename/save buffer): >8 letters -> digraphs (draft names need ~171 pairs).
- **Relocate** only 0-terminated strings whose every slot is a plain pointer with no length immediate (long shop /
  message dialogue), repointing all slots.
- Name entry: the kana pages of the grid (0x0BCC44) become Latin; default names レオ/ティーナ -> Leo/Tina.
- Messages with mid-string pointers (msg 5, mobile 37) are paged/scrolled pieces: keep the piece structure.
