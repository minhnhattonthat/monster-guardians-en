"""Generate tbl/jp11.tbl (story font, 11x11) and tbl/jp9.tbl (battle/menu font, 9x9) from the glyph rows below.

Codes are u16 LE glyph indices; one row = 16 glyphs. Read from tools/font.py sheets; '?' after a glyph in NOTES
means the reading was uncertain at 11/9 px. Box-drawing / blank cells are named explicitly.

    python -X utf8 tools/mktbl.py
"""
from pathlib import Path

# 11x11 font (0x0D3144, 685 glyphs). 0x0B0-0x157 is the name-entry grid (JIS order); the rest is script order.
F11 = [
    '神のいな世界に、繁栄どは無！だか',
    'ら私が使わされた。テスト彼１２３',
    '４５をみつけ近づてきクリム「こで',
    '伝説魔獣完成する中型体と合んじゃ',
    'ばえ君古城跡へ向ベンガ野望阻止」',
    'よそませ次ず０６７８９ワシ研究し',
    'おっ一部解・調べ最初幼出来～バル',
    'ロア王国ヴァダィーナ庭突然目前ザ',
    'ゴラミレ現ぞ▼【】』『ＢＧチェッ',
    '用Ａボタ進フイホドウあくメＬＶ以',
    '上ノヘビブュハエグォ僕ご子息女■',
    '　ＣＤＥＦＨＩＪＫＭＮＯＰＱＲＳ',
    'ＴＵＷＸＹＺａｂｃｄｅｆｇｈｉｊ',
    'ｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
    'ぁぃぅうぇぉぎぐげざぜちぢぬねぱ',
    'ひびぴふぶぷぺほぼぽむめもやゅゆ',
    'ょりろゥオカキギケゲコサジズセゼ',
    'ソゾヂツヅデニヌネパヒピプペポマ',
    'モャヤユョヨヲ，．：；？／＼＋－',
    '±×÷＝≠＜＞￥＄％＃＆＊＠（）',
    '→←↑↓”’［］＾＿｛｝｜゛゜￣',
    '┌─┐│└┘┬┴共巨大匹空天地血',
    '戦広百年文化消去人敗火山下助持外',
    '間暗黒時代陸常類危機存在永遠命権',
    '力掌握支配互対峙征服塗争長末全生',
    '見二引連術挑壮絶繰傷負深姿隠勝利',
    '換取自身尽救技者居後々男盛噴煙口',
    '祭思廃墟残追今再復讐弱足元何感朝',
    '里離達声聞手逃衛兵名捕様渡謝礼背',
    '唖事行倒屋老寝起嫌乗言少昨日件語',
    '始主貴族小雨降法直属騎士団乱入占',
    '拠首謀軍顧問仕公爵高司令官理由立',
    '組織協疑示濡衣捜索邪容赦混分父覚',
    '的家仇訓練不作方処旅知壇震気暴振',
    '狙裏付遅面激活任友会唸告抱込飛運',
    '道至難極登数切揺底怒狂着朽果殿待',
    '祝届崩赤嵐瞬例準備我可能久表情明',
    '違格変貌決写横発議光帯包宙浮強返',
    '場魂話実氾濫秩序遺影響複系受継心',
    '結局想瀕死重産記憶失供判弟本当育',
    '動抑精杯昔因関係度所帰詮同程先炎',
    '攻差恨落殺壁骸探歩焼確信断延♪考',
    '構耐撃防御識必反敵従順回避',
]
# 9x9 font (0x0CDED4, 317 glyphs): battle and menu text.
F9 = [
    'モンスターを選んでください命令決',
    'めて指示の対象全部に出します個別',
    'ど狙うかコマド戦闘終了クリア条件',
    '一　敵倒：えみつけ攻撃る待機そ場',
    '立ち止捕獲定イテム拾逃げろら守れ',
    'ガわボ集中プレヤポトが足りせとな',
    '通信準備きた押無制限ラ賞金０ＧＬ',
    'ｖ５１以上３～６２参加パィ入っ成',
    '績勝負引分４７８９。Ｂキャセルエ',
    'ケブ確認Ａ相手作！【】行阻む魔獣',
    '殲滅襲達追よ警城内ザゴ岩番人森先',
    '住者物蘇武士伏放ミグニ砂漠廃墟跡',
    '見張合ベ最形態現級記録破壊削除完',
    'デは残念ワッへ切替フ管理編シ処名',
    '前変更メジ表状略必要情報、只今設',
    'こ修為未位置／外操装解強化ダウ時',
    '小与大受軽減移動ピ速殺技や反性良',
    'ぶ服従回避功率保存仲間事あサ関連',
    '調整自ヘ力択音楽ＯＮＦ効果ァ閲覧',
    '続じ在生耐久防御知識索順能',
]
# 0x7530-0x7541: control codes (font struct +0x14..+0x18); 0x7FFF ends a string. Handlers: table 0x0C7460
# (8 B per code), load-time expansions 0x0C74D0. Arg counts = calls to 0x080810D8 (read u16) per handler.
# Names are provisional until the marker build shows each effect.
CTRL = {
    0x7530: '{br}', 0x7531: '{page}', 0x7532: '{clear}', 0x7533: '{c7533}', 0x7534: '{wait:2}',
    0x7535: '{c7535:4}', 0x7536: '{c7536}', 0x7537: '{c7537:2}', 0x7538: '{c7538:4}', 0x7539: '{c7539:4}',
    0x753A: '{c753A}', 0x753B: '{col:2}', 0x753C: '{colend}', 0x753D: '{c753D}',
    0x753E: '{word1:2}', 0x753F: '{word2:2}', 0x7540: '{name}', 0x7FFF: '{end}',
}


def rows_to_table(rows, extra_names):
    lines, i = [], 0
    for row in rows:
        for ch in row:
            name = extra_names.get(i, ch)
            lines.append('%02X%02X=%s' % (i & 0xFF, i >> 8, r'\s' if name == ' ' else name))
            i += 1
    for code, name in sorted(CTRL.items()):
        lines.append('%02X%02X=%s' % (code & 0xFF, code >> 8, name))
    return lines, i


GRID = 0x0CFB82   # name-entry grid: u16 glyph11 indices, 0x00AF = unused cell, 0x7FFF end
GRID_EXTRA = {0x191: '支', 0x192: '配', 0x193: '常'}  # 8x8 font tiles past the grid's kanji (seen in VRAM)


def grid_table(rom, f11):
    """8x8 BG font (menus): tile index == name-entry grid index, so its table comes from the grid."""
    import struct
    lines, i = [], 0
    while True:
        c = struct.unpack_from('<H', rom, GRID + 2 * i)[0]
        if c == 0x7FFF:
            break
        if c != 0xAF and i < 0x1A0:  # 0x1A0+ rows hold stray a-f markers, not font tiles
            lines.append('%02X%02X=%s' % (i & 0xFF, i >> 8, r'\s' if f11[c] == ' ' else f11[c]))
        i += 1
    lines += ['%02X%02X=%s' % (i & 0xFF, i >> 8, ch) for i, ch in sorted(GRID_EXTRA.items())]
    return lines


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    out = root / 'tbl'
    out.mkdir(exist_ok=True)
    for name, rows, n_expect, extra in (('jp11', F11, 685, {}), ('jp9', F9, 317, {})):
        lines, n = rows_to_table(rows, extra)
        assert n == n_expect, (name, n)
        (out / (name + '.tbl')).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
        print(name, n, 'glyphs')
    f11 = ''.join(F11)
    lines = grid_table((root / 'rom' / 'mg_jp.gba').read_bytes(), f11)
    (out / 'jp8.tbl').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print('jp8', len(lines), 'tiles')
