"""Build-time VWF: typeset English with a proportional font, slice it into fixed-pitch cells and encode each cell as
an extra glyph of the game's font. The game draws one 16x16 OBJ per glyph at a pitch of font width + 1
(11px story font: 12 px, 9px menu font: 10 px), so a cell holds 2-3 letters instead of one.

Font art: 'char X' + rows of '#'/'.'; advance = last inked column + 2 (1 px gap); space = SPACE px.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPACE = 3
# font key -> (art file, art rows to skip at top, glyph rows, cell pitch px)
FONTS = {
    11: (ROOT / 'font' / 'en11.txt', 1, 11, 12),
    9: (ROOT / 'font' / 'en9.txt', 0, 9, 10),
}


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
    def __init__(self, size=11):
        art, skip, self.rows, self.cell = FONTS[size]
        self.glyphs = {}
        for ch, rows in parse_art(art.read_text(encoding='utf-8')).items():
            px = [[c == '#' for c in r] for r in rows[skip:skip + self.rows]]
            assert len(px) == self.rows, (size, ch)
            cols = [x for x in range(len(rows[0])) if any(r[x] for r in px)]
            w = SPACE if ch == ' ' else (cols[-1] + 2 if cols else SPACE)
            self.glyphs[ch] = (px, w)

    def width(self, text):
        return sum(self.glyphs[ch][1] for ch in text)

    def missing(self, text):
        return sorted({ch for ch in text if ch not in self.glyphs})

    def draw(self, text):
        """-> self.rows pixel rows (lists of bool) of the whole run."""
        rows = [[False] * self.width(text) for _ in range(self.rows)]
        x = 0
        for ch in text:
            px, w = self.glyphs[ch]
            for y in range(self.rows):
                for i, v in enumerate(px[y]):
                    if v and x + i < len(rows[y]):
                        rows[y][x + i] = True
            x += w
        return rows

    def ncells(self, text):
        return max(1, -(-self.width(text) // self.cell))

    def cells(self, text):
        """Render a run and slice it into cell-wide pieces -> list of glyph byte strings."""
        rows = self.draw(text)
        return [encode_cell([r[c * self.cell:(c + 1) * self.cell] for r in rows], self.rows)
                for c in range(self.ncells(text))]


def encode_cell(rows, h):
    """Rows of up to 16 px -> glyph bytes: TL rows 0-7, TR rows 0-7, BL rows 8.., BR rows 8.. (MSB = left)."""
    def byte(r, x0):
        return sum(1 << (7 - i) for i in range(8) if x0 + i < len(r) and r[x0 + i])
    out = bytearray()
    for y0, y1 in ((0, min(8, h)), (8, h)):
        for x0 in (0, 8):
            out += bytes(byte(rows[y], x0) for y in range(y0, y1))
    return bytes(out)


if __name__ == '__main__':
    for size, bpg in ((11, 22), (9, 18)):
        f = Font(size)
        assert len(encode_cell([[True] * f.cell] * f.rows, f.rows)) == bpg
        s = 'There is no prosperity in a world without gods.'
        print(size, f.width(s), 'px,', f.ncells(s), 'cells, missing', f.missing(s + 'ABCXYZ0189?!'))
