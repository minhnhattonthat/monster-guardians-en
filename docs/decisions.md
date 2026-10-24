# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-13 | Honorifics and name order | keep (-san), drop; JP or Western order | Drop honorifics, Western order. |
| D2 | 2026-10-13 | Romanization source for names | official art, earlier patch, Hepburn | Official English (Konami material) where it exists, else Hepburn. |
| D3 | 2026-10-13 | Credits | stay Japanese, translate | English. |
| D4 | 2026-10-13 | Abbreviations | engine work first (default), abbreviate | None: full names and terms, engine changes instead of shortening. |
| D5 | 2026-10-13 | Graphics text left in Japanese | none (default), list | None: title, chapter cards, menus, labels all in scope. |
| D6 | 2026-10-13 | Specs and plans | need approval, pre-approved | Pre-approved; keep going, report at the end. |
| D7 | 2026-10-13 | 8x8 menu text that does not fit | abbreviate, engine work | Engine work: condensed two-letter tiles + run-time tile cache (docs/re/menu8.md). |
| D8 | 2026-10-13 | Battle order names | - | Fight, Wait, Catch, Item, Flee, Guard, Swarm (buttons FIGHT/GUARD/.../ALL/ONE). |
| D9 | 2026-10-20 | Condensed text colour | - | White (ink index 15), as the original font. |
| D10 | 2026-10-20 | Text under a cursor | - | Keep the Japanese one-cell indent (3 spaces in the 9px font). |
| D11 | 2026-10-20 | Monster/item names: wide font when short, condensed when long | mixed, one font | One font: all names condensed, for consistency. |
| D12 | 2026-10-24 | Story scene sound effects | menu font, comic lettering | Comic lettering like the JP hand-drawn effects (Bangers, OFL). |
