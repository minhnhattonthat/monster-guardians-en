"""Monster Guardians glyph fonts: 1bpp, stored per 8x8 tile column-pair: TL rows, TR rows, BL rows, BR rows.

    python -X utf8 tools/font.py sheet ROM OUT.png --font 11|9 [--start N --count N --zoom 3]
"""
import argparse, struct, zlib

# font struct offset -> (w, h, glyph data offset, bytes per glyph, glyph count)
FONTS = {11: 0xD6C24, 9: 0xCF520}


def font_info(rom, size):
    o = FONTS[size]
    w, h, _, ptr, _, bpg = struct.unpack_from('<HHIIII', rom, o)
    base = ptr - 0x08000000
    return w, h, base, bpg, (o - base) // bpg


def glyph(rom, size, i):
    """Rows of pixels (lists of 0/1), h rows x 16 px."""
    w, h, base, bpg, _ = font_info(rom, size)
    b = rom[base + i * bpg: base + (i + 1) * bpg]
    top, bot = min(h, 8), max(0, h - 8)
    rows = [[0] * 16 for _ in range(h)]
    pos = 0
    for r0, n in ((0, top), (8, bot)):
        for col in (0, 8):
            for r in range(n):
                v = b[pos]; pos += 1
                for x in range(8):
                    rows[r0 + r][col + x] = (v >> (7 - x)) & 1
    return rows


def write_png(path, w, h, px):
    raw = b''.join(b'\x00' + bytes(px[y * w:(y + 1) * w]) for y in range(h))
    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


DIGITS = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001',
          '111100111001111', '111100111101111', '111001001001001', '111101111101111', '111101111001111',
          '111101111101101', '110101110101110', '111100100100111', '110101101101110', '111100111100111',
          '111100111100100']  # 3x5 hex digits


def sheet(rom, size, out, start, count, zoom, cols=16):
    _, h, _, _, total = font_info(rom, size)
    count = min(count, total - start)
    cw, ch = 16 * zoom + 4, 16 * zoom + 8
    rows_n = (count + cols - 1) // cols
    W, H = 18 + cols * cw, rows_n * ch
    px = [255] * (W * H)
    def put(x, y, v):
        if 0 <= x < W and 0 <= y < H: px[y * W + x] = v
    for k in range(count):
        i = start + k
        cx, cy = 18 + (k % cols) * cw, (k // cols) * ch
        if k % cols == 0:  # row label: index of first glyph, hex
            for d, ch_ in enumerate('%03X' % i):
                bits = DIGITS[int(ch_, 16)]
                for p, bit in enumerate(bits):
                    if bit == '1': put(1 + d * 4 + p % 3, cy + 6 + p // 3, 0)
        g = glyph(rom, size, i)
        for y in range(h):
            for x in range(16):
                for zy in range(zoom):
                    for zx in range(zoom):
                        put(cx + x * zoom + zx, cy + 2 + y * zoom + zy, 0 if g[y][x] else (255 if x < 12 else 235))
        for y in range(ch):  # cell separator
            put(cx - 2, cy + y, 180)
    write_png(out, W, H, px)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sheet'); s.add_argument('rom'); s.add_argument('out')
    s.add_argument('--font', type=int, default=11); s.add_argument('--start', type=lambda v: int(v, 0), default=0)
    s.add_argument('--count', type=lambda v: int(v, 0), default=10000); s.add_argument('--zoom', type=int, default=3)
    a = ap.parse_args()
    rom = open(a.rom, 'rb').read()
    print(font_info(rom, a.font))
    sheet(rom, a.font, a.out, a.start, a.count, a.zoom)
