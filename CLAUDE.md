# Monster Guardians (GBA) English translation

Skill: translate-retro-game (H:/translation/monster-guardians/.claude/skills/translate-retro-game/SKILL.md).
Read it before ROM, text or QA work. `$S` below = `.claude/skills/translate-retro-game/scripts`.

## Commands (repo root; `python`, never `python3`)
- Build:   `python -X utf8 tools/insert.py` -> build/mg_en.gba (`--marker`, `--qa ID=TEXT`, `--width BANK=PX`).
  Runs: story/ui9 VWF cells, 8x8 menu text (tools/menu8.py), name fields (tools/records.py), graphics jobs
  (tools/gfx.py), then armips asm/menu8.asm (tools/armips/armips.exe, gitignored).
- Check:   `python -X utf8 tools/check.py` (unittest + lint; the pre-commit hook runs this)
- Batches: `python -X utf8 tools/batches.py split|check|merge|fix ...` (work/tl/; briefs docs/translator-brief*.md)
- Extract: `tools/dump.py` (story, ui9), `tools/menu8.py dump` (8x8 banks); tables `tools/mktbl.py`.
- Smoke:   `python -X utf8 $S/emu.py build/mg_en.gba --out work/qa/smoke --frames 3000 --shot-every 300 --sheet --smoke`
- Cold tour: `--route tools/routes/newgame.txt --frames 40000 --mash 40 --mash-key a` (title ~f9840, menu ~f36000).
  `tools/lua/textlog.lua` + `tools/textcheck.py` = story strings cut off by timed scenes.

## Paths
- JP ROM `rom/mg_jp.gba` (No-Intro, CRC 93815CDE). Mesen `tools/mesen2/` + Firmware/gba_bios.bin: **QA in Mesen**.
- Text: `script/story.json` (11px), `ui9.json` (9px), `m8_*.json` (8x8), `names.json` (monster/item names).
- RE notes: `docs/re/README.md` (fonts, story/ui9), `docs/re/menu8.md` (8x8 engine + pair cache),
  `docs/graphics.md` (graphics survey). Glossary + rulings: `glossary.md`. Style: `docs/style-reference.md`.
- Savestates: `work/states/` (menu.mss, stage1_select.mss, battle1_start.mss: made with older builds - VRAM in
  states keeps old graphics/text; cold boot to verify graphics).

## Rulings
- Edit source files only with the file-edit tool. Honorifics dropped, Western order, official names else Hepburn,
  credits English, all graphics text in scope, no abbreviations (engine work instead), pre-approved (report at end).
- 8x8 text: user chose engine work: condensed pair codes + run-time tile cache (docs/re/menu8.md).
- Orders: Fight, Wait, Catch, Item, Flee, Guard, Swarm (button labels FIGHT/GUARD/.../ALL/ONE).

## Status (2026-10-14)
- Done: all text banks (story, ui9, m8 menu/shop/msg/itemdesc/stage/mobile/link/port), 8x8 engine, 523 name
  fields, Leo/Tina, Latin keyboard, graphics (title, 3 cards, class tiles, buttons, 9 scene SFX), reviews (story,
  m8 Critical/Important fixed). RC v1.0: `python -X utf8 tools/release.py 1.0` -> release/ (local, unpublished);
  cold-boot tour to menu/map OK, 0 truncated strings.
- Open: 17 m8 Minor review notes (work/review/m8.report.md); chapters 2-3 + shops/fusion/link/password screens
  not toured in-emulator; free space 0x79B3C0 of 0x7A0000 (pair table at 0x7A0000).
- Release command: `python -X utf8 tools/release.py VERSION`. Never publish without the user.
