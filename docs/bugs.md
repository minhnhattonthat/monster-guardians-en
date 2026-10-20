# Bugs

Tick `- [x] (fixed in <build>)` once re-checked from the cited state.

## 2026-10-19 playtest - mg_en.gba sha1 bb70d8dce672
Evidence: `work/playtest/2026-10-19/NNNN.png|.sheetK.png|.<state>`, presses in `log.tsv`.
Fix build adcb8bfc29b8: re-checked by replaying `log.tsv` from a cold boot (Mesen).

- [x] (fixed in adcb8bfc29b8) **Hero name variable prints as spaced fullwidth glyphs** (steps 0038-0050, every use).
  Shown: `"It was  L e o"`, `reached for  L e o, when`, `L e o's father, Winslow,`, `baton to  L e o.`
  Fix: `asm/story.asm` per-glyph advance; {name} letters remapped to proportional glyphs (grid 0x0CFB82).
- [x] (fixed in adcb8bfc29b8) **Highlighted (pink) words carry trailing padding spaces** (steps 0010-0054,
  systemic): `A  man  stood`, `Then a Monster Tamer   appeared,`, `Monster Knights  .His grounds`, ...
  Fix: runs after a control code now start where the previous run's ink ended (same advance table).
- [x] (fixed in adcb8bfc29b8) **Wrap breaks before punctuation / mid-word** (steps 0043, 0054). Fix: layout wraps
  whole words across controls and measures {word1}/{word2} (widest variant) and {name}.
- [x] (fixed in adcb8bfc29b8) **Empty dialogue page** (step 0042). Cause: after {c7533} the engine numbers the
  first line 1 and breaks it itself at 16 glyph cells. Fix: every story line capped at 15 cells.
- [x] (not a bug) **"Canon" under Sortie on Home Base** (step 0057): the ROM string is カノン (default team names
  カノン/ベッフル/ファーブス at 0x0BD5B2-, copied by 0x080552DA); the JP Home Base shows カノン there too.
- [x] (fixed in adcb8bfc29b8) **Two fonts in one menu** (Yes/No, element select): `"condense": true` on No (every
  copy), Holy, Dark forces the condensed pair font.
- [x] (no change) "Main Beaury": both it and "Heavy Gau" are in `glossary.md` (monster table). No official
  English release exists; kept, consistent with Main Gau / Linbeaury / Chinbeaury.
- [x] (fixed in adcb8bfc29b8) Space before ellipses / after opening quote: same cause as the padding ({c7535}).
- [x] (fixed in adcb8bfc29b8) Pages holding one stranded word: layout widow control (a page break that leaves one
  word alone is redone one word earlier); "with{clear}X" splits in 0D15E6/0D2730 joined. Left as in JP: the
  `{word1:0008}!"` reveal page in 0D0DCE (JP has the same page break).
- [x] (fixed in adcb8bfc29b8) Odd exclamation in narration (0024): now a full stop.
- [x] (fixed in adcb8bfc29b8) "the Legendary Monster Tamer" highlighted at 0049 (and 0D2BA8, 0D2C4C).
- [x] (fixed in adcb8bfc29b8) Title subtitle banner repeated the logo: banner left blank (katakana inpainted).
- [x] (fixed) Shop dialogue box empty / unreadable (2026-10-20, state `H:\emulator\mesen\SaveStates\mg_shop.mss`,
  also in v1.0): the shop typewriter drawer 0x08027EE8 wrote raw pair codes to the BG map (no cache hook).
  Hooked in `asm/menu8.asm`; "Hey, welcome! Good to see you." etc. now shown.
- [x] (fixed) Japanese left on the battle map preview (2026-10-20, state
  `H:\emulator\mesen\SaveStates\mg_battle_map.mss`): hint sprite Ⓑ➔もどる (raw tiles 0x45279C, not in the
  graphics survey) -> "Back" via gfx.job_back_hint.
- [x] (not a bug) Home Base (0057): lowercase `no 1/2/3` is the JP graphic, and the JP tooltip box sits in the same
  place over LV/EXP (checked on the JP ROM at the same point).
- [x] (fixed) Options and other 8x8 menus: condensed pair text purple instead of white. Pair tiles used ink index 5;
  the ROM font uses 15 (tools/font8.py INK). Also fixes the class-name tiles 0x1A0-0x1BF.
- [x] (fixed) Battle menu (`mg_battle_menu.mss`): "Clear Condition" text under the cursor. The JP string indents both
  lines by one full-width cell; EN now indents both lines with 3 spaces (9 px) (ui9 0CCDD0).
- [x] (fixed, not seen in game) Order descriptions (ui9 0CD3DC-0CD4DC): line 1 indented 3 spaces to match the JP
  one-cell indent (JP line 2 is not indented). Probably shown with Options > Help ON; savestate had none on screen.
- [x] (fixed) Battle result (`mg_battle_result.mss`): Time row "...+125 Gold" one tile left. Row format
  `%s    %02d:%02d  %s%s%s%+4d %s` (0x0C2E38) assumes a 3-tile label (じかん); "Time" was 2 pair tiles. EN now
  "Time  " (3 tiles; m8_stage 0C6066).
- [x] (fixed) Stage briefing (`mg_battle_status.mss`): short names (Griffon, Imp) in the wide font next to condensed
  long ones (Mini Golem). All 523 name fields now condensed (records.build passes condense=True).
