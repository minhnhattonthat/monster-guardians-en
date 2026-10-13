# UI (9px font) addendum - batches ui*

Read docs/translator-brief.md first; everything there applies, with these differences.

- These are system strings: menu help lines, battle prompts and orders, clear conditions, save/link messages.
  Register: short, clear, imperative/descriptive like a modern game UI ("Switch to the world map.").
- Hard limit: the check renders each string at 110 px per line (about 22 characters) and allows 2 lines. If it
  says "3 lines", rephrase tighter without losing meaning (no abbreviations). Report `LONG:` if impossible.
- The Japanese pads with fullwidth spaces (　) to push the rest onto the second line or into columns. In English
  write `{br}` where the second line must start, e.g.
  `【クリア条件】　　　　行く手を阻む魔獣を殲滅` -> `[Clear Condition]{br}Wipe out the monsters in your way`
  `　【命令：戦え】　　　敵をみつけて攻撃する` -> `[Order: Fight]{br}Find enemies and attack`
- Strings that are tables or contain Yes/No choices (several space-separated words with gaps, e.g.
  `データをセーブしますか　はい　　いいえ`, `対戦成績　勝　　　負　　　引き分け`, `無制限級 ... 賞金０Ｇ`):
  translate them, keep the same number of items, separate items with {br} where the JP starts a new line, and
  report each id as `UNSURE: id - layout` so the layout can be checked in-game.
- Terms: 命令 = Order; orders 戦え Fight, 待機 Wait, 捕獲 Capture, アイテム Item, 逃げろ Flee, 守れ Guard,
  ボコれ/ポコれ Gang Up; クリア条件 = Clear Condition; 出撃 = sortie (出撃設定 = set as the sortie party);
  修行 = training; パーティ編成 = party formation; ブリーフィング = Briefing; 殲滅 = wipe out;
  パラメータ stat names: 生命 Life, 耐久 Stamina, 攻撃 Attack, 防御 Defense, 行動 Action, 知識 Wisdom,
  必殺技 Special, 反撃 Counter, 索敵 Search, 従順 Obedience, 命中 Accuracy, 回避 Evasion, 技能 Skill.
