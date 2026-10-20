"""8x8 BG font (menus): condensed two-letters-per-tile glyphs from font/cond8.txt.

Original glyphs (ROM font 0x0BEDF0) use palette index 15 = ink, 1 = 1 px outline. Tiles: 4bpp, 8x8, low nibble = left pixel.

    python -X utf8 tools/font8.py preview "Text to show" OUT.png [--pal work/qa/menu1/ppu.pal.bin --pal-index N]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vwf  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / 'font' / 'cond8.txt'
FONT8 = 0x0BEDF0   # 512 raw 4bpp tiles (tile index == text code)
INK, EDGE = 15, 1


def load_art():
    out = {}
    for ch, rows in vwf.parse_art(ART.read_text(encoding='utf-8')).items():
        assert len(rows) == 8 and all(len(r) == 3 for r in rows), ch
        out[ch] = [[c == '#' for c in r] for r in rows]
    return out


ARTS = load_art()


def pair_pixels(a, b):
    """8x8 index grid for the pair 'ab' (each char in a 4 px cell), with a 1 px outline like the original."""
    ink = [[False] * 8 for _ in range(8)]
    for cell, ch in enumerate((a, b)):
        for y, row in enumerate(ARTS[ch]):
            for x, v in enumerate(row):
                if v:
                    ink[y][cell * 4 + x] = True
    px = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            if ink[y][x]:
                px[y][x] = INK
            elif any(0 <= y + dy < 8 and 0 <= x + dx < 8 and ink[y + dy][x + dx]
                     for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                px[y][x] = EDGE
    return px


def tile_bytes(px):
    return bytes(px[y][x] | (px[y][x + 1] << 4) for y in range(8) for x in range(0, 8, 2))


def preview(text, out, pal=None, pal_index=0):
    """Render text as pair tiles at 1x and 3x for eyeballing."""
    import struct, zlib
    if len(text) % 2:
        text += ' '
    tiles = [pair_pixels(text[i], text[i + 1]) for i in range(0, len(text), 2)]
    colors = [(0, 0, 0)] * 16
    if pal:
        p = Path(pal).read_bytes()
        for i in range(16):
            v = struct.unpack_from('<H', p, (pal_index * 16 + i) * 2)[0]
            colors[i] = ((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8)
    else:
        colors[INK], colors[EDGE] = (255, 255, 255), (60, 60, 90)
    z = 3
    w, h = 8 * len(tiles) * z, 8 * z
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            t = tiles[x // z // 8]
            row += bytes(colors[t[y // z][x // z % 8]])
        rows.append(b'\x00' + bytes(row))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    Path(out).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                          + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['preview'])
    ap.add_argument('text')
    ap.add_argument('out')
    ap.add_argument('--pal')
    ap.add_argument('--pal-index', type=int, default=0)
    a = ap.parse_args()
    preview(a.text, a.out, a.pal, a.pal_index)
