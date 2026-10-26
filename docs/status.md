# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 (release). Last build: after the 2026-10-24 agent-playtest fixes.
- **2026-10-24:** 4 agent playtests (`docs/bugs.md`): hooked battle unit panel (0x0800DEA6) and party popup
  (0x0803DE48), stat-box plotters draw glyph column 0, item-card word wrap, font consistency, Goal/Quit Battle,
  pair cache writes every enabled BG's font copy (map labels), Mission: label, fusion price line.
  Fresh new-game state on the current build: `work/qa/cold/end.mss` (old states hold pre-condense names: don't
  judge names/cache tiles from them). `docs/playtester-brief.md` has this game's notes.
- **Done:** all text banks (story, ui9, m8 menu/shop/msg/itemdesc/stage/mobile/link/port), 8x8 engine (condensed
  pairs + tile cache), 523 name fields (all condensed), Leo/Tina, Latin keyboard, graphics (title, 3 chapter cards,
  class tiles, battle buttons, 9 scene SFX, battle-map "Back" hint), reviews (story, m8 Critical/Important).
  2026-10-19 playtest bugs all closed (`docs/bugs.md`): story-font per-glyph advance (asm/story.asm), word-level
  wrap + widow control, 15-cell line cap, shop typewriter, white condensed text, cursor gaps, Time-row alignment.
- **Released:** v1.1 (2026-10-24, GitHub release v1.1): 2026-10-19/20/24 playtest fixes.
- **2026-10-26, issue #1 (unreleased):** port map corrupted (m8 msg bank ran 8 bytes into the port tile set header
  0x0A1A38: range fixed, bogus entries dropped, test added); fusion result labels garbled (char animator
  0x080625D0/0x08062666 hooked); 使用中/修行中 small tags drawn as IN USE / TRAINING (gfx.job_tags).
  States: `work/issue1/{port,fus,eq2}/` (from `work/pt/world` in the main checkout).
- **Open:**
  - Status tags: TRAINING (small) not seen in game yet; 64x32 修行中 (0x50FA18 + cap 0x50FE18) still Japanese.
  - Order descriptions (ui9 0CD3DC-0CD4DC) indented but not seen in game (probably Options > Help ON).
  - 17 m8 Minor review notes (work/review/m8.report.md).
  - Chapters 2-3, shops other than the first, link and password screens not toured in-emulator.
  - Free space used to 0x79CFB8 of 0x7A0000 (pair table at 0x7A0000).
- **Waiting on the user:** title banner left blank (no "Monster Guardians" overlay): keep or draw text?
