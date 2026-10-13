"""Build the English ROM: typeset script/*.json English into pre-rendered glyph cells, append the cells to the game
fonts, write the strings to free space and repoint every slot. Original Japanese strings stay in place, unreferenced.

    python -X utf8 tools/insert.py [--marker] [--qa ID=TEXT ...] [--out build/mg_en.gba]

--marker  every untranslated string becomes '<ID> ...' filler at about twice the JP length (controls kept).
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import romlib  # noqa: E402
import vwf  # noqa: E402

FREE_START, FREE_END = 0x770000, 0x800000
# bank -> font size, font struct offset, original glyph count, layout (line px, lines per page)
BANKS = {
    'story': dict(font=11, struct=0x0D6C24, nglyphs=685, width=204, lines=2),  # 17 cells, measured in-game
    'ui9': dict(font=9, struct=0x0CF520, nglyphs=317, width=110, lines=2),
}
NAME_CHARS = 6            # player name length budget for wrapping ({name} = one 12 px OBJ per character)
PAGE = '{clear}'          # control emitted when a page fills up (story: waits for A, then clears)
# Auto-advancing intro: {page} scrolls ONE line up (no wait) and {clear} clears without waiting, so a full page
# gets a timed wait and one {page} per line on screen.
AUTO = (0x0CFF84, 0x0D03E8)
AUTO_WAIT = '{wait:003C}'
# u32 data patches: offset -> (JP value, new value). Scene ops are 5 words [op, a, b, c, d]; op 0x28 sets
# owner var a = b, var 2 = frames per glyph. The intro runs on a timer, so English cells must type faster.
PATCHES = {
    0x0C8D5C: (5, 3),   # intro scene: glyph delay 5 -> 3
}
TOKEN = re.compile(r'(\{[^}]*\})')
FILLER = 'the quick brown fox jumps over a lazy dog and then '


class Free:
    def __init__(self, rom, start=FREE_START, end=FREE_END):
        self.rom, self.pos, self.end = rom, start, end
        if any(rom[start:end]):  # the JP ROM pads with 0x00 from 0x767660
            raise SystemExit(f'free space {start:06X}-{end:06X} is not blank')

    def put(self, data, align=4):
        self.pos = (self.pos + align - 1) & ~(align - 1)
        if self.pos + len(data) > self.end:
            raise SystemExit('out of free space')
        off = self.pos
        self.rom[off:off + len(data)] = data
        self.pos += len(data)
        return off


class Glyphs:
    """Original glyph array + appended English cells (deduplicated)."""

    def __init__(self, rom, struct_off, n):
        self.struct = struct_off
        ptr = struct.unpack_from('<I', rom, struct_off + 8)[0] - romlib.BASE
        self.bpg = struct.unpack_from('<I', rom, struct_off + 16)[0]
        self.data = bytearray(rom[ptr:ptr + n * self.bpg])
        self.n, self.index = n, {}

    def code(self, cell):
        if cell not in self.index:
            self.index[cell] = self.n + len(self.index)
            self.data += cell
            if self.index[cell] >= 0x7530:
                raise SystemExit('glyph codes ran into the control-code range')
        return self.index[cell]

    def commit(self, rom, free):
        off = free.put(bytes(self.data))
        struct.pack_into('<I', rom, self.struct + 8, romlib.BASE + off)


def parse(text):
    """-> list of ('text', str) / ('ctl', '{...}')."""
    return [('ctl', p) if TOKEN.fullmatch(p) else ('text', p) for p in TOKEN.split(text) if p]


def layout(text, font, width, lines, name_w, auto=False):
    """English text with controls -> token list of runs ('run', str) and controls ('ctl', '{...}'), with {br} and
    page breaks inserted so that no line exceeds width px (runs start on cell boundaries) and no page exceeds lines.
    auto: intro mode, where {page} scrolls one line: pages end with AUTO_WAIT + one {page} per line shown."""
    out, cur, x0, line = [], '', 0, 0
    cell = font.cell

    def flush():
        nonlocal cur, x0
        if cur:
            out.append(('run', cur))
            x0 += font.ncells(cur) * cell
            cur = ''

    def scroll_all():
        out.extend([('ctl', '{page}')] * (line + 1))

    def newline():
        nonlocal x0, line
        flush()
        if line + 1 >= lines:
            if auto:
                out.append(('ctl', AUTO_WAIT))
                scroll_all()
            else:
                out.append(('ctl', PAGE))
            line = 0
        else:
            out.append(('ctl', '{br}'))
            line += 1
        x0 = 0

    for kind, val in parse(text):
        if kind == 'ctl':
            name = val[1:-1].split(':')[0]
            if name == 'br':
                newline()
            elif name in ('clear', 'page', 'c7533'):
                flush()
                if auto and name == 'page':
                    scroll_all()
                else:
                    out.append((kind, val))
                x0, line = 0, 0
            elif name == 'name':
                flush()
                if x0 + name_w > width:
                    newline()
                out.append((kind, val))
                x0 += name_w
            else:
                flush()
                out.append((kind, val))
            continue
        for word in re.findall(r' *[^ ]+| +$', val):
            cand = cur + word
            if x0 + font.width(cand) > width and (cur.strip() or x0 > 0):
                newline()
                cand = word.lstrip(' ')
            cur = cand
    flush()
    return out


def encode(tokens, font, glyphs):
    codes = []
    for kind, val in tokens:
        if kind == 'run':
            codes += [glyphs.code(c) for c in font.cells(val)]
        else:
            codes += romlib.encode(val, {})
    return codes + [romlib.END]


def marker_text(e):
    """'<ID> filler' replacing the glyph runs of the JP text, about twice as long; controls kept."""
    out, first = [], True
    for kind, val in parse(e['jp']):
        if kind == 'ctl':
            out.append(val)
            continue
        n = 2 * len(val)
        fill = (FILLER * (n // len(FILLER) + 1))[:n].strip()
        out.append((e['id'] + ' ' + fill) if first else fill)
        first = False
    return ''.join(out)


def build(out_path, marker=False, qa=None):
    rom = bytearray(romlib.rom_bytes())
    free = Free(rom)
    for off, (old, new) in PATCHES.items():
        if struct.unpack_from('<I', rom, off)[0] != old:
            raise SystemExit(f'patch {off:06X}: expected {old:#x}')
        struct.pack_into('<I', rom, off, new)
    qa = qa or {}
    stats = {}
    for bank, cfg in BANKS.items():
        path = romlib.ROOT / 'script' / f'{bank}.json'
        font = vwf.Font(cfg['font'])
        glyphs = Glyphs(rom, cfg['struct'], cfg['nglyphs'])
        done = 0
        for e in json.loads(path.read_text(encoding='utf-8')):
            if e['status'] == 'unused' or not e['slots']:
                continue
            text = qa.get(e['id']) or e['en'] or (marker_text(e) if marker else '')
            if not text:
                continue
            miss = font.missing(''.join(v for k, v in parse(text) if k == 'text'))
            if miss:
                raise SystemExit(f'{bank} {e["id"]}: no glyph for {miss}')
            auto = bank == 'story' and AUTO[0] <= int(e['id'], 16) < AUTO[1]
            tokens = layout(text, font, cfg['width'], cfg['lines'], NAME_CHARS * 12, auto)
            codes = encode(tokens, font, glyphs)
            off = free.put(struct.pack('<%dH' % len(codes), *codes), 2)
            for s in e['slots']:
                struct.pack_into('<I', rom, int(s, 16), romlib.BASE + off)
            done += 1
        glyphs.commit(rom, free)
        stats[bank] = (done, len(glyphs.index))
    Path(out_path).parent.mkdir(exist_ok=True)
    Path(out_path).write_bytes(rom)
    for bank, (n, cells) in stats.items():
        print(f'{bank}: {n} strings, {cells} cells')
    print(f'free space used to {free.pos:06X}; wrote {out_path}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--marker', action='store_true')
    ap.add_argument('--qa', action='append', default=[], help='ID=TEXT override')
    ap.add_argument('--out', default=str(romlib.ROOT / 'build' / 'mg_en.gba'))
    ap.add_argument('--width', action='append', default=[], help='BANK=PX line width override (measuring)')
    a = ap.parse_args()
    for w in a.width:
        bank, px = w.split('=')
        BANKS[bank]['width'] = int(px)
    build(a.out, a.marker, dict(q.split('=', 1) for q in a.qa))
