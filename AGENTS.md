# Monster Guardians (GBA) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root; `python`, never `python3`)
- Build:   `python -X utf8 tools/insert.py` -> build/mg_en.gba (checks the dump against `rom.sha1` first;
  `--marker`, `--qa ID=TEXT`, `--width BANK=PX`). Runs: story/ui9 VWF cells, 8x8 menu text (tools/menu8.py), name
  fields (tools/records.py), graphics jobs (tools/gfx.py), then armips asm/menu8.asm (tools/armips/armips.exe v0.11.0, gitignored).
- Check:   `python -X utf8 tools/check.py` (unittest + lint; the pre-commit hook runs this)
- Batches: `python -X utf8 tools/batches.py split|check|merge|fix ...` (work/tl/; briefs docs/translator-brief*.md)
- Extract: `tools/dump.py` (story, ui9), `tools/menu8.py dump` (8x8 banks); tables `tools/mktbl.py`.
- Smoke:   `python -X utf8 $SKILL/scripts/emu.py build/mg_en.gba --out work/qa/smoke --frames 3000 --shot-every 300 --sheet --smoke`
- Cold tour: `--route tools/routes/newgame.txt --frames 40000 --mash 40 --mash-key a` (title ~f9840, menu ~f36000).
  `tools/lua/textlog.lua` + `tools/textcheck.py` = story strings cut off by timed scenes.
- Release: `python -X utf8 tools/release.py VERSION` -> release/ (BPS patch + verify, README, zip; never publish without the user)

## Paths
- Original ROM: `rom/mg_jp.gba` (gitignored; No-Intro, CRC 93815CDE; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`).
  Emulator: Mesen 2 in `tools/mesen2/` + Firmware/gba_bios.bin (gitignored): **QA in Mesen**.
- Text: `script/story.json` (11px), `ui9.json` (9px), `m8_*.json` (8x8), `names.json` (monster/item names). Tables: `tbl/`.
- RE notes: `docs/re/README.md` (fonts, story/ui9), `docs/re/menu8.md` (8x8 engine + pair cache),
  `docs/graphics.md` (graphics survey). Glossary: `glossary.md`. Style: `docs/style-reference.md`. Fonts: `docs/fonts.md`.
- Savestates: `work/states/` (menu.mss, stage1_select.mss, battle1_start.mss: made with older builds - VRAM in
  states keeps old graphics/text; cold boot to verify graphics).

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- 8x8 text: condensed pair codes + run-time tile cache (docs/re/menu8.md). Hooked drawers are listed there; a new
  screen with garbled menu text is usually an unhooked drawer.
- Fixed-layout rows (printf formats at 0x0C2E00-0x0C2E80, label + padding) assume the Japanese label's tile count:
  pad the English label to the same number of tiles.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
