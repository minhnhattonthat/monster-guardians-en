"""Shared ROM + text helpers: u16 glyph-code strings (11px story font, 9px menu font).

Strings are u16 LE codes: glyph index (< 0x7530), control 0x7530-0x7540 with u16 args, 0x7FFF end.
Text form: glyphs as table chars, controls as {name} or {name:XXXX,YYYY} (hex args), unknown codes [XXXX].
"""
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / 'rom' / 'mg_jp.gba'
BASE = 0x08000000
END = 0x7FFF
# code -> (name, argc); names match tools/mktbl.py CTRL
CTRL = {
    0x7530: ('br', 0), 0x7531: ('page', 0), 0x7532: ('clear', 0), 0x7533: ('c7533', 0), 0x7534: ('wait', 1),
    0x7535: ('c7535', 2), 0x7536: ('c7536', 0), 0x7537: ('c7537', 1), 0x7538: ('c7538', 2), 0x7539: ('c7539', 2),
    0x753A: ('c753A', 0), 0x753B: ('col', 1), 0x753C: ('colend', 0), 0x753D: ('c753D', 0),
    0x753E: ('word1', 1), 0x753F: ('word2', 1), 0x7540: ('name', 0),
}
CTRL_BY_NAME = {n: (c, a) for c, (n, a) in CTRL.items()}
TOKEN = re.compile(r'\{(\w+)(?::([0-9A-Fa-f,]+))?\}|\[([0-9A-Fa-f]{4})\]')


def rom_bytes():
    return ROM.read_bytes()


def load_table(name):
    """tbl/<name>.tbl -> (code->char, char->code) for glyph codes only."""
    dec = {}
    for line in (ROOT / 'tbl' / f'{name}.tbl').read_text(encoding='utf-8').splitlines():
        k, v = line.split('=', 1)
        code = int(k[2:4] + k[:2], 16)
        if code < 0x7530:
            dec[code] = ' ' if v == r'\s' else v
    return dec, {v: k for k, v in dec.items()}


def read_codes(rom, off):
    """-> list of u16 codes up to and including END, following control args."""
    out = []
    while True:
        c = struct.unpack_from('<H', rom, off)[0]
        off += 2
        out.append(c)
        if c == END:
            return out
        for _ in range(CTRL.get(c, (None, 0))[1]):
            out.append(struct.unpack_from('<H', rom, off)[0])
            off += 2


def decode(codes, dec):
    """codes (without END) -> text."""
    out, i = [], 0
    while i < len(codes):
        c = codes[i]
        i += 1
        if c in CTRL:
            name, argc = CTRL[c]
            args = codes[i:i + argc]
            i += argc
            out.append('{%s%s}' % (name, ':' + ','.join('%04X' % a for a in args) if args else ''))
        elif c in dec:
            out.append(dec[c])
        else:
            out.append('[%04X]' % c)
    return ''.join(out)


def encode(text, enc):
    """text -> codes (without END); inverse of decode."""
    out, i = [], 0
    while i < len(text):
        m = TOKEN.match(text, i)
        if m:
            if m[3]:
                out.append(int(m[3], 16))
            else:
                code, argc = CTRL_BY_NAME[m[1]]
                args = [int(a, 16) for a in m[2].split(',')] if m[2] else []
                if len(args) != argc:
                    raise ValueError(f'{m[0]}: expected {argc} args')
                out += [code] + args
            i = m.end()
        else:
            out.append(enc[text[i]])
            i += 1
    return out


def valid_string(rom, off, nglyphs, limit=2000):
    """True when a well-formed string (glyphs < nglyphs or known controls) ends at END within limit codes."""
    n = 0
    while off + 2 <= len(rom) and n < limit:
        c = struct.unpack_from('<H', rom, off)[0]
        off += 2
        n += 1
        if c == END:
            return n > 1
        if c in CTRL:
            off += 2 * CTRL[c][1]
        elif c >= nglyphs:
            return False
    return False


def pointer_slots(rom):
    """{target file offset: [slot offsets]} for every aligned u32 that looks like an even ROM address."""
    slots = {}
    for s in range(0, len(rom) - 3, 4):
        v = struct.unpack_from('<I', rom, s)[0]
        if BASE <= v < BASE + len(rom) and not v & 1:
            slots.setdefault(v - BASE, []).append(s)
    return slots
