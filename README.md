# Monster Guardians English translation

Unofficial English fan translation of **Monster Guardians** (Game Boy Advance, Konami / Mobile21, 2001, Japan only):
the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Story dialogue | Translated (chapters 2-3 checked by tools and review, not played through in full) |
| Menus, shops, battle prompts, item and monster names | Translated |
| Title screen, chapter cards, battle buttons, drawn sound effects | Translated (the katakana banner under the logo is left blank) |
| Status tags (IN USE / TRAINING) | Partly translated (the large 修行中 tag is still Japanese) |
| Name entry | Translated (Latin keyboard) |
| Link, Mobile Adapter and password screens | Translated, not checked in play |

Known issues: odd-length names end in a half-space ("Golem Light ,"); the chapter-card glow can show a faint copy of the
title (as in the original); password entry may show odd characters.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `asm/` | Engine changes (armips): condensed menu font with a run-time tile cache, story-font spacing. |
| `font/`, `tbl/` | English fonts (pixel art as text) and the game's character tables. |
| `tests/` | unittest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |

## Build your own patched ROM

Needs Python 3.12+ with Pillow (`pip install pillow`), [armips](https://github.com/Kingcom/armips) v0.11.0 at
`tools/armips/armips.exe` (Windows build), and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/monster-guardians-en
cd monster-guardians-en
# copy your dump to: rom/mg_jp.gba
#   (8,388,608 bytes, SHA-1 350351b03349728a8ff0a5b0985ad62df7baacc9; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/insert.py                         # -> build/mg_en.gba
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Konami's and is included only so
the translation can be checked against it. Monster Guardians is (c) 2001 Konami / Mobile21; this project is not
affiliated with them. Do not share patched ROMs. The chapter-card font is STIX and the sound-effect font is Bangers (both SIL Open Font License, `font/`).

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
