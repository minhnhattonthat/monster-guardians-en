# Monster Guardians (GBA) English translation

Skill: translate-retro-game (H:/translation/monster-guardians/.claude/skills/translate-retro-game/SKILL.md).
Read it before ROM, text or QA work. `$S` below = `.claude/skills/translate-retro-game/scripts`.

## Commands (repo root; `python`, never `python3`)
- Tables:  `python -X utf8 tools/mktbl.py` -> tbl/jp11.tbl, tbl/jp9.tbl (glyph rows live in mktbl.py)
- Fonts:   `python -X utf8 tools/font.py sheet rom/mg_jp.gba out.png --font 11|9 --start N --count 64`
- Check:   `python -X utf8 tools/check.py` (unittest + lint; the pre-commit hook runs this)
- Smoke:   `python -X utf8 $S/emu.py <rom> --out work/qa/smoke --frames 3000 --shot-every 300 --sheet --smoke`

## Paths
- JP ROM `rom/mg_jp.gba` (copy of the No-Intro dump, gitignored). Mesen `tools/mesen2/` (+ Firmware/gba_bios.bin,
  gitignored): **QA in Mesen** (user ruling). QA output `work/qa/`, savestates `work/states/`.
- RE notes: `docs/re/README.md` (fonts, encoding, control codes, text ranges). Glossary + rulings: `glossary.md`.

## Rulings
- Edit source files only with the file-edit tool. Honorifics dropped, Western name order, official names else
  Hepburn, credits English, all graphics text in scope, no abbreviations. Pre-approved: report at the end.

## Status
- Done: Step 0, recon of text system (both fonts decoded, control codes mapped).
- Next: graphics-text survey, extract/identity build, pre-rendered proportional cells for English (see notes).
