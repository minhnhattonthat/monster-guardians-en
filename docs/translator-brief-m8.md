# Menu text (8x8 tile font) addendum - batches m8*

Read docs/translator-brief.md first (style, glossary, ASCII, report format); these rules override it for m8 batches.

## The format
- Text is drawn with 8x8 tiles and is stored **in place**: each entry has a fixed number of tiles (the `limit`
  column: lines x width, and a total). Japanese uses one tile per character.
- English fits in two ways, chosen automatically: **normal** (1 character per tile, nicer) or **condensed**
  (2 characters per tile, small letters). Aim for normal where you can do it without losing meaning; use the
  condensed room (twice the characters) when the meaning needs it. Never abbreviate words.
- `/` is a line break, in both the Japanese and your English. Your English may use at most the same number of
  lines as the Japanese, each line within the width. Spaces count.
- `{pal:N}` changes text colour: keep each one, in the same order, around the equivalent words.
- Usable characters: A-Z a-z 0-9 space . , ! ? ' " - : ( ) & + and in normal mode also % ~ * = ;
  No other symbols (no `/` inside text: it is the line break).

## Fragments
Many entries are pieces of one message: the game prints them in order with a name, number or item between them,
e.g. `この２タイをゴウセイすると、` `デンセツのモンスター` `/「` [monster name] `」になるようじゃ。/ゴウセイには`
[gold] `かかるが、よいな？`. Translate the pieces so the whole reads naturally in English **with the variable in
the same place** (you may move words between neighbouring pieces). A piece that is only `は、` or `の` may become
a short English connector (`'s`, ` is`, ` now`) or a single space; an empty result is not allowed - use a space.
Report pieces whose variable you had to guess as `UNSURE: id - variable?`.

## Terms
- Use glossary.md (Monsters table for monster names). Keep the menu style terse but complete:
  けってい = OK, キャンセル = Cancel, はい/いいえ = Yes/No, なまえ = Name, ぞくせい = Element,
  ごうせい = Fusion, しゅつげき = Sortie, しゅぎょう = Training, パーティ = Party, へんせい = Formation.
- Elements: でんせつ Legend, カゼ Wind, ミズ Water, ホノオ Fire, ダイチ Earth, シンセイ Holy, アンコク Dark.
- Stats: いのち Life, たいきゅう Stamina, こうげき Attack, ぼうぎょ Defense, こうどう Action, ちしき Wisdom,
  ひっさつわざ Special, はんげき Counter, さくてき Search, じゅうじゅん Obedience, めいちゅう Accuracy,
  かいひ Evasion, ぎのう Skill.
- Gold stays `Gold` (the game prints `Ｇｏｌｄ`/`Ｇ`), LV = `LV`, EXP = `EXP`, PP = `PP` (game's own labels).
- Klimt (fusion shop, じゃ/のう) keeps his grumpy old-man voice; shopkeepers are gruff traders.
- Mobile Adapter / link messages: plain, polite system English (`Please check the cable.`). ＣＯＤＥ：xx-xxx stays.

## Validate
`python -X utf8 tools/batches.py check <batch>` prints OK or the exact overflow per id.
