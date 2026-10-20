# Monster Guardians (GBA, Konami 2001) - RE notes

ROM: `Monster Guardians (Japan).gba`, 8 MiB, CRC32 93815CDE, SHA-1 350351b03349728a8ff0a5b0985ad62df7baacc9
(No-Intro verified). Header `MONSTERGUARD` / `AMNJ` / maker `A4`. Used data ends at 0x76765D; 0x767660-0x7FFFFF free
(0xFF fill, ~1.1 MiB).

## Text system (both fonts)

- Text is **u16 LE glyph indices** into a per-font bitmap array, not Shift-JIS (`jp_left --sjis` finds only debug
  strings at 0x0C5CCC). Codes 0x7530-0x7541 are control codes, 0x7FFF ends a string.
- Font struct (24 B): `u16 w, u16 h, u32 0x40000000, u32 glyphs_ptr, u32 4 (tiles), u32 bytes_per_glyph,
  u32 ctrl_lo 0x7530, u32 ctrl_hi 0x7541`.
  - 11x11 story font: struct 0x0D6C24, glyphs 0x0D3144, 22 B/glyph, 685 glyphs. Refs: 0x062A34, 0x07EF7C.
  - 9x9 menu/battle font: struct 0x0CF520, glyphs 0x0CDED4, 18 B/glyph, 317 glyphs. Refs: 0x00ECD8, 0x06292C.
- Glyphs are 1bpp, stored as tile quadrants: TL rows (8 or h), TR rows, BL rows (h-8), BR rows; MSB = left pixel
  (`tools/font.py`). Glyph order = first appearance in the script, except 11px 0x0B0-0x157 = name-entry grid
  (JIS order). Tables: `tools/mktbl.py` -> `tbl/jp11.tbl`, `tbl/jp9.tbl` (readings checked against decoded text).
- Rendering (11px story): each glyph becomes its own 16x16 OBJ (4bpp), cell pitch 12 px; glyph bitmap expanded at
  0x0807D384 into EWRAM 0x02001170, CpuSet to OBJ VRAM. Object slots per box: 34 (0x0808102C `cmp r3,#0x21`).
- put-glyph 0x08081010 (one caller, 0x08080F30): cursor x at obj+0x448 (px; OBJ x = x << 5), y +0x44A, glyphs on
  the line +0x44C (the 17th on line 1 / 16th on line 2 breaks the line itself), line +0x44E. It added font w + 1;
  `asm/story.asm` hooks 0x0808107E to add a per-code advance from a table built by `tools/insert.py` for the
  story font (English cells end where their ink ends; {name} letters proportional via the grid table 0x0CFB82,
  whose only reader is the {name} expansion at 0x0808140C).
- Interpreter object (EWRAM, e.g. 0x02000AAC): `+0x0C` owner, `+0x10` font struct, `+0x48` u16 text buffer,
  `+0x450` read index, `+0x460` source ptr, `+0x464` buffer write ptr.
  - Loader 0x08081450 copies the source string into the buffer; codes with a load-time handler
    (table 0x0C74D0: 753E/753F/7540) expand instead of copying.
  - Runtime handlers: table 0x0C7460, 8 B per code (func, flag). Args read via 0x080810D8 (one u16 each).

### Control codes (u16 args)
| code | args | name | notes |
|---|---|---|---|
| 7530 | 0 | {br} | line break |
| 7531 | 0 | {page} | wait / new page (auto mode aware) |
| 7532 | 0 | {clear} | wait for button, clear box |
| 7533 | 0 | {c7533} | after location headers |
| 7534 | 1 | {wait} | pause N frames |
| 7535 | 2 | {c7535} | slow/print-speed section? `{c7535 1,X}...・・・{c7536}` |
| 7536 | 0 | {c7536} | end of 7535 |
| 7537 | 1 | {c7537} | speaker/portrait? at scene starts |
| 7538, 7539 | 2 | | screen effects? |
| 753B | 1 | {col} | colour on (arg = palette, usually 2) |
| 753C | 0 | {colend} | colour off |
| 753E | 1 | {word1} | insert string from table 0x0C7410 (by player gender/state) |
| 753F | 1 | {word2} | insert string from table 0x0C73F0 (ご子息/ご息女...) |
| 7540 | 0 | {name} | player name: grid indices at owner+0xEC, mapped via grid table 0x0CFB82 |

## Text locations (pointer-referenced, `work/strscan.py`)
- 0x0CC90E-0x0CDED4: 9px UI strings (orders, clear conditions, menu help, save, stats).
- 0x0CF9A0-0x0D3144: 11px: kinsoku lists (0x0CF9A0-0x0CF9C3, data), debug, monster/word tables (0x0CFA1E-),
  name-entry grid table 0x0CFB82 (data), story 0x0CFF84-0x0D30F3, stat names 0x0D30F4-.
- 0x0CC800-0x0CC90D and 0x0CF58C-0x0CF7A6: not text (glyph usage lists).

## Graphics text (survey in progress)
- Title logo katakana subtitle, chapter title cards (第1章 ...), world-map/menu labels (しゅつげき, めいれい,
  メッセージ, つうしん, モンスター...): tiles, not text.

## Emulator
- Mesen (`tools/mesen2/`, BIOS in `Firmware/`); real BIOS adds ~270 frames vs mGBA. Intro starts ~f750.
- Probes: `tools/lua/execregs.lua` (regs at an exec address), `tools/lua/copylog.lua` (BIOS CpuSet to VRAM).
