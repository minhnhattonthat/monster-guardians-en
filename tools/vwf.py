"""Build-time VWF for the 11px story font: typeset English with a proportional font, slice it into 12 px cells and
encode each cell as an extra glyph of the game's font (the game draws one 16x16 OBJ per glyph at a 12 px pitch).

Font art: font/en11.txt ('char X' + 13 rows of 6 '#'/'.'); art rows 1-11 become glyph rows 0-10.
Width of a glyph = last inked column + 2 (1 px gap); space = SPACE px.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / 'font' / 'en11.txt'
CELL = 12          # px advance per glyph object
ROWS = 11          # glyph rows in the 11x11 font
SPACE = 3


def parse_art(text):
    glyphs, cur = {}, None
    for line in text.splitlines():
        if line.startswith('char '):
            name = line[5:]
            cur = ' ' if name == 'space' else name
            glyphs[cur] = []
        elif line and set(line) <= {'.', '#'} and cur is not None:
            glyphs[cur].append(line)
    return glyphs


class Font:
    def __init__(self, art=ART):
        self.glyphs = {}
        for ch, rows in parse_art(Path(art).read_text(encoding='utf-8')).items():
            px = [[c == '#' for c in r] for r in rows[1:1 + ROWS]]
            cols = [x for x in range(len(rows[0])) if any(r[x] for r in px)]
            w = SPACE if ch == ' ' else (cols[-1] + 2 if cols else SPACE)
            self.glyphs[ch] = (px, w)

    def width(self, text):
        return sum(self.glyphs[ch][1] for ch in text)

    def missing(self, text):
        return sorted({ch for ch in text if ch not in self.glyphs})

    def draw(self, text):
        """-> ROWS pixel rows (lists of bool) of the whole run."""
        rows = [[False] * self.width(text) for _ in range(ROWS)]
        x = 0
        for ch in text:
            px, w = self.glyphs[ch]
            for y in range(ROWS):
                for i, v in enumerate(px[y]):
                    if v and x + i < len(rows[y]):
                        rows[y][x + i] = True
            x += w
        return rows

    def cells(self, text):
        """Render a run and slice it into CELL-wide cells -> list of 22-byte glyphs."""
        rows = self.draw(text)
        n = max(1, -(-len(rows[0]) // CELL))
        return [encode_cell([r[c * CELL:(c + 1) * CELL] for r in rows]) for c in range(n)]


def encode_cell(rows):
    """Rows of up to 16 px -> glyph bytes: TL rows 0-7, TR rows 0-7, BL rows 8-10, BR rows 8-10 (MSB = left)."""
    def byte(r, x0):
        return sum(1 << (7 - i) for i in range(8) if x0 + i < len(r) and r[x0 + i])
    out = bytearray()
    for y0, y1 in ((0, 8), (8, ROWS)):
        for x0 in (0, 8):
            out += bytes(byte(rows[y], x0) for y in range(y0, y1))
    return bytes(out)


if __name__ == '__main__':
    f = Font()
    assert len(encode_cell([[True] * 12] * ROWS)) == 22
    s = 'There is no prosperity in a world without gods.'
    print(f.width(s), 'px,', len(f.cells(s)), 'cells', f.missing(s))
