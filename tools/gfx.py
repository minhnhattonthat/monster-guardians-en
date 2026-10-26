"""Graphics text: LZSS resources (decoder 0x08081B48), 4bpp tiles <-> indexed pixels, and per-item edit jobs.

A resource is [u32 decompressed size][LZSS data]; the resource table (0x0DA000-) holds the header pointer, the data
pointer and the compressed size next to each other. Edited resources are recompressed into free space and every
table word pointing at the old header/data is repointed (size word after the data pointer updated).

    python -X utf8 tools/gfx.py preview JOB OUT.png     # render the edited area of a job for eyeballing
Jobs are applied by tools/insert.py (apply_all).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lz  # noqa: E402
import romlib  # noqa: E402

ROOT = romlib.ROOT
TABLE = (0x0D8000, 0x0DE000)


def resource(rom, data_off, comp_size):
    return lz.lzss_decompress(rom[data_off:data_off + comp_size])


def tiles_to_px(data, n_tiles_w, tile_ids):
    """Compose tiles (4bpp, tile t at data[t*32]) laid out row-major n_tiles_w wide -> list of pixel rows."""
    rows_t = (len(tile_ids) + n_tiles_w - 1) // n_tiles_w
    px = [[0] * (n_tiles_w * 8) for _ in range(rows_t * 8)]
    for k, t in enumerate(tile_ids):
        if t is None:
            continue
        tx, ty = k % n_tiles_w, k // n_tiles_w
        b = data[t * 32:t * 32 + 32]
        for y in range(8):
            for x in range(8):
                v = b[y * 4 + x // 2]
                px[ty * 8 + y][tx * 8 + x] = (v >> 4) if x & 1 else (v & 0xF)
    return px


def px_to_tiles(data, n_tiles_w, tile_ids, px):
    """Write pixels back into the tiles they came from (later duplicates of a tile id win)."""
    data = bytearray(data)
    for k, t in enumerate(tile_ids):
        if t is None:
            continue
        tx, ty = k % n_tiles_w, k // n_tiles_w
        b = bytearray(32)
        for y in range(8):
            for x in range(0, 8, 2):
                b[y * 4 + x // 2] = px[ty * 8 + y][tx * 8 + x] | px[ty * 8 + y][tx * 8 + x + 1] << 4
        data[t * 32:t * 32 + 32] = b
    return bytes(data)


def repoint(rom, old_hdr, new_hdr, new_size):
    """Repoint table words: header ptr old_hdr -> new_hdr, data ptr old_hdr+4 -> new_hdr+4 (+ size after it)."""
    n = 0
    for o in range(TABLE[0], TABLE[1], 4):
        v = struct.unpack_from('<I', rom, o)[0]
        if v == romlib.BASE + old_hdr:
            struct.pack_into('<I', rom, o, romlib.BASE + new_hdr)
            n += 1
        elif v == romlib.BASE + old_hdr + 4:
            struct.pack_into('<II', rom, o, romlib.BASE + new_hdr + 4, new_size)
            n += 1
    if not n:
        raise SystemExit(f'no table entry for resource {old_hdr:06X}')
    return n


def store(rom, free, old_hdr, data):
    comp = lz.lzss_compress(data)
    blob = struct.pack('<I', len(data)) + comp
    off = free.put(blob, 4)
    repoint(rom, old_hdr, off, len(comp))
    return off


def inpaint(px, box, ink, fill):
    """Replace `ink` colours inside box (x0, y0, x1, y1) with the nearest `fill` colour on the same row."""
    x0, y0, x1, y1 = box
    src = [r[:] for r in px]
    h, w = len(px), len(px[0])
    for y in range(y0, y1):
        for x in range(x0, x1):
            if src[y][x] not in ink:
                continue
            for d in range(1, 40):   # nearest fill pixel on the square ring at distance d
                ring = [(x + dx, y + dy) for dx in range(-d, d + 1) for dy in (-d, d)] + \
                       [(x + dx, y + dy) for dy in range(-d + 1, d) for dx in (-d, d)]
                hits = [src[yy][xx] for xx, yy in ring if 0 <= xx < w and 0 <= yy < h and src[yy][xx] in fill]
                if hits:
                    px[y][x] = max(set(hits), key=hits.count)
                    break


def draw_text(px, text, size, cx, y, color):
    """Draw text with tools/vwf.py font `size`, centred on cx, top row y."""
    import vwf
    f = vwf.Font(size)
    rows = f.draw(text)
    x0 = cx - len(rows[0]) // 2
    for yy, r in enumerate(rows):
        for xx, v in enumerate(r):
            if v:
                px[y + yy][x0 + xx] = color


# ---- jobs ------------------------------------------------------------------------------------------------
def job_title(rom, free=None, preview=None):
    """Title logo banner: the katakana reading of the logo is inpainted away (BG1 rows 13-16); English lettering
    there only repeated the logo (2026-10-19 playtest), so the banner stays blank."""
    hdr, data_off, size = 0x14F1D8, 0x14F1DC, 0x163A
    data = resource(rom, data_off, size)
    # BG1 map rows 13-16 (title screen): tile value - 1 = resource tile; values <= 2 are blank
    layout = [(13, 1, 0x06F, 28), (14, 2, 0x08B, 27), (15, 4, 0x0A4, 22), (16, 5, 0x0BA, 20)]
    ids = [None] * (30 * 4)
    for k, (row, col, first, n) in enumerate(layout):
        for i in range(n):
            ids[k * 30 + col + i] = first + i - 1
    px = tiles_to_px(data, 30, ids)
    inpaint(px, (52, 12, 194, 26), ink={1, 2, 3, 4, 5, 6, 7, 8, 9}, fill={10, 11, 12, 13, 14, 15})
    if preview:
        pal = [((x & 31) * 8, (x >> 5 & 31) * 8, (x >> 10 & 31) * 8) for x in struct.unpack_from('<16H', rom, 0x14F1B8)]
        img = to_image(px, pal)
        img.resize((img.width * 4, img.height * 4)).save(preview)
        return
    store(rom, free, hdr, px_to_tiles(data, 30, ids, px))


CARDS = [   # (chapter label, title) for the 3 chapter cards
    ('Chapter 1', 'Ambition by Design'),
    ('Chapter 2', 'Past and Present...'),
    ('Chapter 3', 'What It Means to Be Human'),
]
CARD_TABLE = 0x0D92B0   # 6 layers x 0x44 bytes: per chapter a crisp layer then a glow layer


def card_layers(rom):
    """-> [(pal, tiles hdr, tiles off, tiles size, map hdr, map off, map size)] for the 6 card layers."""
    out = []
    for k in range(6):
        w = struct.unpack_from('<17I', rom, CARD_TABLE + k * 0x44)
        out.append(tuple(x - romlib.BASE if x >= romlib.BASE else x
                         for x in (w[0], w[2], w[4], w[5], w[7], w[9], w[10])))
    return out


def render_card_text(label, title, glow):
    """Intensity image (L, 256x160) of the card text; glow = blurred, brighter version."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    font_path = str(ROOT / 'font' / 'STIXGeneral.ttf')
    img = Image.new('L', (256, 160), 0)
    d = ImageDraw.Draw(img)
    for text, size, y in ((label, 12, 47), (title, 16, 66)):
        f = ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.BASIC)
        w = d.textlength(text, font=f)
        x = 120 - w / 2
        for dx in (0, 1):   # faux bold
            d.text((x + dx, y), text, fill=255, font=f)
    if glow:
        img = img.filter(ImageFilter.GaussianBlur(1.5))
        img = img.point(lambda v: min(255, int(v * 1.6)))
    return img


def tiles_and_map(img, max_tiles, pal_bits):
    """Quantise an L image to 16 levels, cut 8x8 tiles (deduplicated, tile 0 blank) -> (tile bytes, map bytes)."""
    w, h = img.size
    q = [[(img.getpixel((x, y)) * 15 + 127) // 255 for x in range(w)] for y in range(h)]
    tiles, index, mp = [bytes(32)], {bytes(32): 0}, [0] * (32 * 32)
    for ty in range(h // 8):
        for tx in range(w // 8):
            b = bytearray(32)
            for y in range(8):
                for x in range(0, 8, 2):
                    b[y * 4 + x // 2] = q[ty * 8 + y][tx * 8 + x] | q[ty * 8 + y][tx * 8 + x + 1] << 4
            b = bytes(b)
            if b not in index:
                index[b] = len(tiles)
                tiles.append(b)
            mp[ty * 32 + tx] = index[b] | (pal_bits if index[b] else 0)
    if len(tiles) > max_tiles:
        raise SystemExit(f'card text needs {len(tiles)} tiles (room for {max_tiles})')
    return b''.join(tiles).ljust(max_tiles * 32, b'\0'), struct.pack('<1024H', *mp)


def job_cards(rom, free=None, preview=None):
    layers = card_layers(rom)
    shots = []
    for ch, (label, title) in enumerate(CARDS):
        for g in (0, 1):
            pal, thdr, toff, tsize, mhdr, moff, msize = layers[ch * 2 + g]
            old_tiles = resource(rom, toff, tsize)
            old_map = struct.unpack('<1024H', resource(rom, moff, msize))
            pal_bits = next((e & 0xF000 for e in old_map if e & 0x3FF), 0)
            img = render_card_text(label, title, g)
            tiles, mp = tiles_and_map(img, len(old_tiles) // 32, pal_bits)
            if preview:
                shots.append(img)
                continue
            store(rom, free, thdr, tiles)
            store(rom, free, mhdr, mp)
    if preview:
        from PIL import Image
        sheet = Image.new('L', (512, 160 * 3))
        for k, im in enumerate(shots):
            sheet.paste(im, ((k % 2) * 256, (k // 2) * 160))
        sheet.save(preview)


CLASS_TILES = [   # 8x8 font tiles 0x1A0-0x1BF: pre-drawn class names, 4 tiles each
    'Minotaur', 'Griffon', 'Gremlin', 'Tempest', 'Garizunt', 'Behemoth', 'Fafnir', 'Legend']


def job_class_tiles(rom, free=None, preview=None):
    import font8
    for k, name in enumerate(CLASS_TILES):
        text = name.center(8)
        for i in range(4):
            code = 0x1A0 + k * 4 + i
            tile = font8.tile_bytes(font8.pair_pixels(text[2 * i], text[2 * i + 1]))
            if not preview:
                rom[font8.FONT8 + code * 32:font8.FONT8 + code * 32 + 32] = tile


def draw_cond(px, text, cx, y, color, arts=None):
    """Proportional text with the condensed 8x8 glyphs (font/cond8.txt): advance = ink width + 1. -> width.
    `arts` overrides glyphs by character."""
    import font8
    glyphs = []
    for ch in text:
        art = (arts or {}).get(ch) or font8.ARTS[ch]
        cols = [x for x in range(3) if any(r[x] for r in art)]
        glyphs.append((art, (cols[-1] + 1) if cols else 2))
    width = sum(w + 1 for _, w in glyphs) - 1
    x = cx - width // 2
    for art, w in glyphs:
        for yy, r in enumerate(art):
            for xx in range(w):
                if r[xx]:
                    px[y + yy][x + xx] = color
        x += w + 1
    return width


BUTTONS = 0x0EB0D8   # order buttons: 32x16 sprites, 8 raw 4bpp tiles (0x100 bytes) each
BUTTON_WORDS = {'たたかえ': 'FIGHT', '守れ': 'GUARD', 'にげろ': 'FLEE', 'アイテム': 'ITEM',
                'ポコれ': 'SWARM', 'ほかく': 'CATCH', 'たいき': 'WAIT'}   # 22x7 px inside the button
BUTTON_LIST = {   # block index -> JP word (read from the rendered sheet)
    3: 'たたかえ', 4: '守れ', 5: 'にげろ', 6: 'アイテム', 7: 'ポコれ',
    8: 'たたかえ', 9: '守れ', 10: 'にげろ', 11: 'アイテム', 12: 'ほかく', 13: 'たいき', 14: 'たたかえ', 15: '守れ',
    16: 'にげろ', 17: 'アイテム', 18: 'ポコれ', 19: 'ほかく', 20: 'たいき', 21: 'たたかえ', 22: '守れ', 23: 'にげろ',
    24: 'アイテム', 25: 'ポコれ', 26: 'たたかえ', 27: '守れ', 28: 'にげろ', 29: 'アイテム', 30: 'ほかく', 31: 'たいき',
}


def relabel(px, box, text):
    """Inside box: the most common colour is the fill, the next the ink; clear it and centre the new text."""
    from collections import Counter
    x0, y0, x1, y1 = box
    c = Counter(px[y][x] for y in range(y0, y1) for x in range(x0, x1)).most_common()
    fill = c[0][0]
    ink = c[1][0] if len(c) > 1 else fill
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[y][x] = fill
    draw_cond(px, text, (x0 + x1) // 2, y0 + (y1 - y0 - 7) // 2, ink)


TARGET_BUTTONS = 0x0ED138   # 6 buttons: ぜんたい (all) / たんたい (single) alternating, 3 colour sets
BUTTON_WORDS.update({'ぜんたい': 'ALL', 'たんたい': 'ONE'})


def job_buttons(rom, free=None, preview=None):
    out = []
    items = [(BUTTONS + i * 0x100, jp) for i, jp in BUTTON_LIST.items()]
    items += [(TARGET_BUTTONS + k * 0x100, 'ぜんたい' if k % 2 == 0 else 'たんたい') for k in range(6)]
    for off, jp in items:
        ids = list(range(8))
        px = tiles_to_px(rom[off:off + 0x100], 4, ids)
        relabel(px, (5, 4, 27, 11), BUTTON_WORDS[jp])
        if preview:
            out.append(px)
        else:
            rom[off:off + 0x100] = px_to_tiles(rom[off:off + 0x100], 4, ids, px)
    if preview:
        from PIL import Image
        p = [(i * 16, i * 16, i * 16) for i in range(16)]
        sheet = Image.new('RGB', (8 * 36, 4 * 20))
        for k, px in enumerate(out):
            sheet.paste(to_image(px, p).convert('RGB'), ((k % 8) * 36, (k // 8) * 20))
        sheet.resize((sheet.width * 3, sheet.height * 3), 0).save(preview)


SFX = [   # story pictures with hand-drawn sound effects: (palette, tiles hdr, tiles off, size, map off, size, edits)
    # Ancient castle scene, man with the baton: ゴゴ (left) / ゴゴゴ (right) -> RUMBLE. Boxes in 256x256 map px.
    (0x1002D4, 0x1002F4, 0x1002F8, 0x1882, 0x101B80, 0x309, [((48, 52, 92, 84), 'RUMBLE', '', (53, 50, 96, 84)),
                                                             ((136, 46, 192, 84), 'RUMBLE')]),
    # Ruins, monsters attack the pursuers: light lettering ドガッ / バキッ on the dark backdrop
    (0x540858, 0x540878, 0x54087C, 0x0C17, 0x541498, 0x216, [((28, 48, 92, 108), 'WHAM!', 'light'),
                                                             ((152, 52, 214, 108), 'CRACK!', 'light')]),
    (0x543008, 0x543028, 0x54302C, 0x0C70, 0x543CA0, 0x210, [((28, 48, 92, 108), 'WHAM!', 'light'),   # Tina
                                                             ((152, 52, 214, 108), 'CRACK!', 'light')]),
    # monsters charging: ドドドド (white, spills below the picture: fill may be transparent)
    (0x4A85B8, 0x4A85D8, 0x4A85DC, 0x2120, 0x4AA700, 0x36B, [((14, 86, 158, 132), 'THUD THUD THUD', 'light0')]),
    (0x4AAA80, 0x4AAAA0, 0x4AAAA4, 0x225C, 0x4ACD04, 0x366, [((14, 86, 158, 132), 'THUD THUD THUD', 'light0')]),
    (0x4C6678, 0x4C6698, 0x4C669C, 0x2898, 0x4C8F38, 0x3BC, [((6, 94, 98, 138), 'KA-BOOM!', 'light0')]),
    (0x4CA62C, 0x4CA64C, 0x4CA650, 0x1788, 0x4CBDDC, 0x2A3, [((146, 52, 186, 76), 'WHACK', 'white',
                                                              (138, 42, 189, 76))]),
    (0x521180, 0x5211A0, 0x5211A4, 0x14FB, 0x5226A4, 0x2EB, [((62, 38, 94, 70), 'CLANG', 'white',
                                                              (57, 32, 104, 72))]),
]


def scene_px(rom, toff, tsize, moff, msize):
    """-> (tiles, map entries, 256x256 pixels as shown: map flips applied)."""
    tiles = resource(rom, toff, tsize)
    mp = struct.unpack('<1024H', resource(rom, moff, msize)[:2048])
    px = [[0] * 256 for _ in range(256)]
    for k, e in enumerate(mp):
        t = e & 0x3FF
        if t * 32 >= len(tiles):
            continue
        cell = tiles_to_px(tiles, 1, [t])
        if e & 0x400:
            cell = [r[::-1] for r in cell]
        if e & 0x800:
            cell = cell[::-1]
        for y in range(8):
            px[k // 32 * 8 + y][k % 32 * 8:k % 32 * 8 + 8] = cell[y]
    return tiles, mp, px


def restore_cells(rom, free, thdr, tiles, mhdr, mapdata, px0, px):
    """Store an edited scene: every map cell whose pixels changed gets a new tile of its own (pictures reuse
    backdrop tiles across the map, so writing into a shared tile would lose the edit in the other cells)."""
    tiles = bytearray(tiles)
    mp = list(struct.unpack_from('<1024H', mapdata))
    for k in range(1024):
        x, y = k % 32 * 8, k // 32 * 8
        if all(px[y + r][x:x + 8] == px0[y + r][x:x + 8] for r in range(8)):
            continue
        n = len(tiles) // 32
        tiles += px_to_tiles(bytes(32), 1, [0], [px[y + r][x:x + 8] for r in range(8)])
        mp[k] = mp[k] & 0xF000 | n
    mapdata = bytearray(mapdata)
    struct.pack_into('<1024H', mapdata, 0, *mp)
    store(rom, free, thdr, bytes(tiles))
    store(rom, free, mhdr, bytes(mapdata))


SFX_FONT = ROOT / 'font' / 'Bangers-Regular.ttf'


def draw_sfx(px, text, box, ink, outline=None, angle=10):
    """Comic lettering for a sound effect: Bangers, rotated `angle` degrees (clockwise, like the stepped JP
    lettering), as large as fits in box (x0, y0, x1, y1) with its 1 px outline; outline colour optional."""
    from PIL import Image, ImageDraw, ImageFont
    x0, y0, x1, y1 = box
    pad = 1 if outline is not None else 0
    for size in range(40, 7, -1):
        f = ImageFont.truetype(str(SFX_FONT), size)
        l, t, r, b = f.getbbox(text)
        im = Image.new('L', (r - l + 4, b - t + 4))
        ImageDraw.Draw(im).text((2 - l, 2 - t), text, font=f, fill=255)
        im = im.rotate(-angle, resample=Image.BICUBIC, expand=True)
        im = im.crop(im.getbbox())
        if im.width + 2 * pad <= x1 - x0 and im.height + 2 * pad <= y1 - y0:
            break
    w, h = im.size
    ox, oy = x0 + (x1 - x0 - w) // 2, y0 + (y1 - y0 - h) // 2
    on = {(x, y) for y in range(h) for x in range(w) if im.getpixel((x, y)) > 110}
    if outline is not None:
        for x, y in on:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) not in on:
                        px[oy + y + dy][ox + x + dx] = outline
    for x, y in on:
        px[oy + y][ox + x] = ink


def job_sfx(rom, free=None, preview=None):
    shots = []
    for pal, thdr, toff, tsize, moff, msize, edits in SFX:
        tiles, _, px = scene_px(rom, toff, tsize, moff, msize)
        px0 = [r[:] for r in px]
        colors = struct.unpack_from('<16H', rom, pal)
        lum = sorted(range(1, 16), key=lambda i: (colors[i] & 31) + (colors[i] >> 5 & 31) + (colors[i] >> 10 & 31))
        for box, text, *rest in edits:
            # mode: '' = dark ink (3 darkest); 'light' = all but the 4 darkest; 'white' = 3 brightest;
            # a trailing '0' lets the fill use transparency (lettering spilling outside the picture).
            # Optional 4th item: area for the English lettering when the JP box is too small or off the picture.
            m = rest[0] if rest else ''
            area = rest[1] if len(rest) > 1 else box
            light = m.startswith(('light', 'white'))
            inks = lum[-3:] if m.startswith('white') else lum[4:] if light else lum[:3]
            ink = inks[-1] if light else inks[0]
            fill = set(range(16)) - set(inks) - (set() if m.endswith('0') else {0})
            inpaint(px, box, ink=set(inks), fill=fill)
            draw_sfx(px, text, area, ink, outline=lum[0] if light else None)
        if preview:
            p = [((x & 31) * 8, (x >> 5 & 31) * 8, (x >> 10 & 31) * 8) for x in colors]
            shots.append(to_image(px, p).convert('RGB'))
            continue
        restore_cells(rom, free, thdr, tiles, moff - 4, resource(rom, moff, msize), px0, px)
    if preview:
        from PIL import Image
        sheet = Image.new('RGB', (512 * len(shots), 512))
        for k, s in enumerate(shots):
            sheet.paste(s.resize((512, 512)), (512 * k, 0))
        sheet.save(preview)


BACK_HINT = 0x45279C   # battle map "(B) -> もどる" hint: 64x16 OBJ, 16 raw 4bpp tiles (rows 1-2 of a 64x32 sprite)


def job_back_hint(rom, free=None, preview=None):
    ids = list(range(16))
    data = rom[BACK_HINT:BACK_HINT + 0x200]
    px = tiles_to_px(data, 8, ids)
    inpaint(px, (29, 3, 55, 13), ink={7, 0xE, 0xF}, fill={5, 0xB, 0xD})
    draw_text(px, 'Back', 9, 43, 4, 0xF)
    if preview:
        to_image(px, [(i * 16, i * 16, i * 16) for i in range(16)]).resize((64 * 6, 16 * 6)).save(preview)
        return
    rom[BACK_HINT:BACK_HINT + 0x200] = px_to_tiles(data, 8, ids, px)


TAG_CAP = 0x50F9D8   # status tags: 8x16 cap (right end, OBJ tile 0x4A) shared by the 32x16 bodies below
# 修行中 (port training), 使用中 (equipped item, issue #1): word, centre x (the word must end by col 31)
TAGS = {0x50F7D8: ('TRAINING', 18), 0x50F8D8: ('IN USE', 20)}
THIN_I = [[1, 0, 0]] * 7 + [[0, 0, 0]]   # 1 px I: TRAINING is 31 px with the serif I, the body holds 28


def job_tags(rom, free=None, preview=None):
    """Status tags 修行中 / 使用中 (piece table 0x510344): body + the shared cap drawn as one 40x16 label. The cap held
    the right half of 中; it becomes a plain frame end, so the English word sits in the body (interior cols 3-31).
    Colours: 1 black outline/fill, 2 dark red frame (cols 2 and 37, rows 1 and 14), 5 red text."""
    cap = rom[TAG_CAP:TAG_CAP + 0x40]
    out = []
    for k, (off, (word, cx)) in enumerate(TAGS.items()):
        px = [b + c for b, c in zip(tiles_to_px(rom[off:off + 0x100], 4, list(range(8))),
                                    tiles_to_px(cap, 1, [0, 1]))]
        for x in range(3, 37):          # the kanji strokes broke the frame with outline pixels
            px[1][x] = px[14][x] = 2
        for y in range(2, 14):
            px[y][2] = px[y][37] = 2
            for x in range(3, 37):
                px[y][x] = 1
        width = draw_cond(px, word, cx, 4, 5, {'I': THIN_I} if len(word) > 6 else None)
        assert cx - width // 2 + width <= 32, word   # the cap is shared: no text in it
        out.append(px)
        if not preview:
            rom[off:off + 0x100] = px_to_tiles(rom[off:off + 0x100], 4, list(range(8)), [r[:32] for r in px])
            if k == 0:
                rom[TAG_CAP:TAG_CAP + 0x40] = px_to_tiles(cap, 1, [0, 1], [r[32:] for r in px])
    if preview:
        from PIL import Image
        pal = [(0, 64, 0), (0, 0, 0), (140, 20, 60)] + [(255, 0, 255)] * 2 + [(230, 60, 110)] + [(255, 0, 255)] * 10
        sheet = Image.new('RGB', (40, 16 * len(out)))
        for k, px in enumerate(out):
            sheet.paste(to_image(px, pal).convert('RGB'), (0, 16 * k))
        sheet.resize((sheet.width * 8, sheet.height * 8), 0).save(preview)


JOBS = {'title': job_title, 'cards': job_cards, 'class_tiles': job_class_tiles, 'buttons': job_buttons,
        'sfx': job_sfx, 'back_hint': job_back_hint, 'tags': job_tags}


def apply_all(rom, free):
    for name, job in JOBS.items():
        job(rom, free)
    return len(JOBS)


def load_palette(path, index):
    p = Path(path).read_bytes()
    out = []
    for i in range(16):
        v = struct.unpack_from('<H', p, (index * 16 + i) * 2)[0]
        out.append(((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8))
    return out


def to_image(px, pal):
    from PIL import Image
    img = Image.new('P', (len(px[0]), len(px)))
    img.putpalette([c for rgb in pal for c in rgb] + [0] * (768 - 48))
    img.putdata([v for row in px for v in row])
    return img


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'preview':
        JOBS[sys.argv[2]](romlib.rom_bytes(), preview=sys.argv[3])
    else:
        print(__doc__)
