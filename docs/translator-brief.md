# Translator brief - Monster Guardians (GBA, Konami 2001)

You translate part of the Japanese script of Monster Guardians into English for a fan patch. A monster-raising
tactics RPG: the young noble {name} (default Leo, or the girl Tina) is hunted after Duke Bellingham seizes Vandam
Castle, and with the old monster researcher Klimt fuses monsters to recreate the Legendary Monster. Tone: earnest
fantasy drama with a grumpy, folksy old man and two dim-witted villain monsters.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - voices and the approved pilot (match it).
2. `glossary.md` - names and terms are binding; spell them exactly.

## Input: `work/tl/<batch>.tsv`
`id<TAB>form<TAB>limit<TAB>Japanese`, in story order (use neighbours for context). Translate each entry as a whole.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII only: straight quotes, `...`, `--`; no tabs
inside the English, no Japanese or fullwidth characters, no `\uXXXX`.

## Control codes (`{...}`) - copy every one exactly, at the matching place in the English
- `{br}` is a Japanese line break: DROP it. The build wraps and pages English automatically. Only keep a `{br}`
  where a break is required for effect (rare). All other codes must appear in the same number as in the Japanese.
- `{clear}` = wait for the A button, then clear the box (a page break the writer chose). Keep each one; put it
  where the English breaks naturally at the same point in the content.
- `{c7533}` follows a location header like `～廃墟～`; render headers as `- The Ruins -`.
- `{wait:XXXX}` = a pause; keep it at the equivalent point.
- `{c7535:XXXX,YYYY}...{c7536}` = typing-speed change around a span (usually `・・・`); keep both around the
  equivalent English span (`...`).
- `{col:0002}...{colend}` = coloured span (names, key terms). Keep both around the equivalent English words.
- `{c7537:XXXX}`, `{c7538:XXXX,YYYY}`, `{c7539:XXXX,YYYY}` = portrait/screen effects: keep at the same position
  (usually the very start).
- `{name}` = the player's name. `{word2:0000}` = "I" (boy or girl), `{word2:0001}` = "son"/"daughter",
  `{word2:0002}` = "Legendary Monster Tamer", `{word2:0003}` = "he"/"she" (chosen by the player's gender).
  `{word1:XXXX}` = the name of the player's legendary-monster stage (e.g. "Golem Light"); treat it as a monster name.
  Write sentences that work for both genders and any name: no a/an before `{name}`/`{word1}`, nothing glued after
  them except `'s`, no "1st/2nd" built on a variable.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add or drop details.
  Jokes and wordplay keep their punch.
- Dialogue: `Speaker: "Line."` - speaker names from the glossary (男 = Man, 老人 = Old Man, 追っ手1 = Pursuer 1).
  Narration has no quotes. Several lines by one speaker between `{clear}`s stay inside one pair of quotes.
- Honorifics dropped (ベリンガム様 = Lord Bellingham; 王 = King). Western name order. No abbreviations anywhere
  (Mount, not Mt.; Level, not Lv.).
- Punctuation: 「」 -> "...", 『』 -> '...', ・・・ -> ..., ！！ -> !!, ！？ -> ?!, ～X～ headers -> - X -.
- Length: English is wrapped at about 38 characters per line, 2 lines per page; there is no hard limit, but keep it
  tight - long-winded lines mean more button presses.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root; fix every reported id until it prints OK.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
