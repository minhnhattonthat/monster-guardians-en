# Graphics text survey (tile-drawn Japanese)

Status: todo / located / done. Shots: work/qa/*.

| # | Where | Japanese | Status | Notes |
|---|---|---|---|---|
| 1 | Title screen, under the logo | モンスターガーディアンズ | done | gfx.job_title: banner inpainted, left blank (lettering only repeated the logo) |
| 2 | Chapter title cards (3) | 第1章 仕組まれた野望 / 第2章 過去と現在と・・・ / 第3章 人であるべき事 | done | gfx.job_cards: STIX serif rendered into the crisp + glow ramps; table 0x0D92B0 |
| 3 | Battle order buttons (sprites, raw tiles 0x0EB0D8 / 0x0ED138) | たたかえ 守れ にげろ アイテム ポコれ ほかく たいき ぜんたい たんたい | done | gfx.job_buttons: FIGHT GUARD FLEE ITEM SWARM CATCH WAIT ALL ONE |
| 4 | 8x8 font tiles 0x1A0-0x1BF (pre-drawn class names) | ミノタウロス ゲリフォン ゲレムリン テンペスト ガリオーント ベヒーモス ファーブニル レジェンド | done | gfx.job_class_tiles (condensed glyphs) |
| 5 | Story scene sound effects | ゴゴゴ (castle), ドガッ/バキッ (ruins) | done | gfx.job_sfx: RUMBLE, WHAM!, CRACK!, THUD, KA-BOOM!, WHACK, CLANG in comic lettering (Bangers, rotated 10°, outlined when light; user request 2026-10-24); later chapters not toured - may hold more |
| 5b | Battle map preview hint (64x16 OBJ, raw tiles 0x45279C) | Ⓑ➔もどる | done | gfx.job_back_hint: "Back" (found 2026-10-20, state mg_battle_map.mss) |
| 5c | Status tags (OBJ, raw tiles; piece table 0x510344, sizes in it) | 修行中 (32x16 0x50F7D8 + cap 0x50F9D8; 64x32 0x50FA18 + cap 0x50FE18), 使用中 (32x16 0x50F8D8) | todo | found by the 2026-10-20 raw-tile sweep; need an in-game shot to confirm how body + cap pieces join |
| 5d | Unreferenced kana/kanji glyph block 0x0AC040-0x0AE1E8 | font | n/a? | no pointer into it found; likely unused |
| 6 | Menu icons (right column) | (pictograms) | n/a | no text |
| 7 | "MISSION START", "Grandate", "Sinker" | English already | n/a | |
