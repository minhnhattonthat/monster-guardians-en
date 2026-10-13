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
    for y in range(y0, y1):
        row = px[y]
        src = row[:]
        for x in range(x0, x1):
            if src[x] in ink:
                for d in range(1, 40):
                    for xx in (x - d, x + d):
                        if 0 <= xx < len(row) and src[xx] in fill:
                            row[x] = src[xx]
                            break
                    else:
                        continue
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
    """Title logo banner: katakana reading of the logo -> small English lettering (BG1 rows 13-16)."""
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
    draw_text(px, 'Monster Guardians', 9, 121, 14, 3)
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


def draw_cond(px, text, cx, y, color):
    """Proportional text with the condensed 8x8 glyphs (font/cond8.txt): advance = ink width + 1. -> width."""
    import font8
    glyphs = []
    for ch in text:
        art = font8.ARTS[ch]
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
    (0x1002D4, 0x1002F4, 0x1002F8, 0x1882, 0x101B80, 0x309, [((48, 52, 92, 84), 'RUMBLE'),
                                                             ((136, 46, 192, 84), 'RUMBLE')]),
    # Ruins, monsters attack the pursuers: light lettering ドガッ / バキッ on the dark backdrop
    (0x540858, 0x540878, 0x54087C, 0x0C17, 0x541498, 0x216, [((28, 48, 92, 108), 'WHAM!', 'light'),
                                                             ((152, 52, 214, 108), 'CRACK!', 'light')]),
]


def scene_px(rom, toff, tsize, moff, msize):
    tiles = resource(rom, toff, tsize)
    mp = struct.unpack('<1024H', resource(rom, moff, msize)[:2048])
    ids = [e & 0x3FF for e in mp]
    return tiles, ids, tiles_to_px(tiles + bytes(32), 32, [i if i * 32 < len(tiles) else None for i in ids])


def job_sfx(rom, free=None, preview=None):
    shots = []
    for pal, thdr, toff, tsize, moff, msize, edits in SFX:
        tiles, ids, px = scene_px(rom, toff, tsize, moff, msize)
        colors = struct.unpack_from('<16H', rom, pal)
        lum = sorted(range(1, 16), key=lambda i: (colors[i] & 31) + (colors[i] >> 5 & 31) + (colors[i] >> 10 & 31))
        for box, text, *mode in edits:
            inks = lum[4:] if mode == ['light'] else lum[:3]
            ink = inks[-1] if mode == ['light'] else inks[0]
            inpaint(px, box, ink=set(inks), fill=set(range(16)) - set(inks) - {0})
            cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2 - 5
            draw_text(px, text, 9, cx, cy, ink)
            draw_text(px, text, 9, cx + 1, cy, ink)   # bold
        if preview:
            p = [((x & 31) * 8, (x >> 5 & 31) * 8, (x >> 10 & 31) * 8) for x in colors]
            shots.append(to_image(px, p).convert('RGB'))
            continue
        used = [i if i is not None and i * 32 < len(tiles) else None for i in ids]
        store(rom, free, thdr, px_to_tiles(tiles, 32, used, px))
    if preview:
        from PIL import Image
        sheet = Image.new('RGB', (512 * len(shots), 512))
        for k, s in enumerate(shots):
            sheet.paste(s.resize((512, 512)), (512 * k, 0))
        sheet.save(preview)


JOBS = {'title': job_title, 'cards': job_cards, 'class_tiles': job_class_tiles, 'buttons': job_buttons,
        'sfx': job_sfx}


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
