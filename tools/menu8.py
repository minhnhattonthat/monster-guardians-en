"""8x8 BG-font text (menus, shops, messages): extract to script/m8_<bank>.json.

Codes are u16 tile indices (tbl/jp8.tbl); 0x1FF = new line, 0x200+n = palette n, 0 = end. Text form: tiles as
table chars, 0x1FF as '/', 0x200+n as {pal:N}, unknown as [XXXX].
A string is split at every 0 and at every pointer target, so packed (unterminated) strings come out one per
pointed-to piece; 'term' says whether a 0 follows it.

    python -X utf8 tools/menu8.py dump [--report]
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import romlib  # noqa: E402

NL = 0x1FF
BANKS = {
    'mobile': [(0x09DB34, 0x0A1108)],
    'msg': [(0x0A12A8, 0x0A1A40)],
    'shop': [(0x0A7FF6, 0x0A9764)],
    'itemdesc': [(0x0B720C, 0x0B78D0)],
    'menu': [(0x0BD388, 0x0BEDC4)],
    'stage': [(0x0C5D9A, 0x0C6DF0)],
}
TOKEN = re.compile(r'\{pal:([0-9A-F]+)\}|\[([0-9A-F]{4})\]')


def decode(codes, dec):
    out = []
    for c in codes:
        if c == NL:
            out.append('/')
        elif 0x200 <= c < 0x300:
            out.append('{pal:%X}' % (c - 0x200))
        elif c in dec and c != 0:
            out.append(dec[c])
        else:
            out.append('[%04X]' % c)
    return ''.join(out)


def encode(text, enc):
    out, i = [], 0
    while i < len(text):
        m = TOKEN.match(text, i)
        if m:
            out.append(0x200 + int(m[1], 16) if m[1] else int(m[2], 16))
            i = m.end()
        elif text[i] == '/':
            out.append(NL); i += 1
        else:
            out.append(enc[text[i]]); i += 1
    return out


# ASCII -> fullwidth table char for the normal 8 px tiles; '/' is reserved for line breaks
ASCII = {' ': '　', '.': '．', ',': '，', '!': '！', '?': '？', ':': '：', ';': '；', '-': '－', "'": '’',
         '"': '”', '(': '（', ')': '）', '&': '＆', '+': '＋', '%': '％', '~': '～', '*': '＊', '=': '＝'}
ASCII.update({c: chr(ord(c) + 0xFEE0) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'})
# font slots the run-time pair cache (asm/menu8.asm) may overwrite in VRAM: kana 0x40-0xE0, kanji row 0x170-0x193
FREE_CODES = list(range(0x40, 0xE1)) + list(range(0x170, 0x194))
TOKEN_EN = re.compile(r'(\{pal:[0-9A-F]+\})')
PAIR_BASE = 0x4000   # 0x200+ and 0x2000-0x200F are palette codes in some drawers; 0x4000-0x63FF is free


def pair_code(p):
    """Condensed pair code: 0x4000 + (a-0x20)*0x60 + (b-0x20); asm/menu8.asm draws it through the tile cache."""
    return PAIR_BASE + (ord(p[0]) - 0x20) * 0x60 + ord(p[1]) - 0x20


def pairs_bin():
    """All 96x96 condensed pair tiles, indexed like pair_code (blank where a character has no glyph)."""
    import font8
    out = bytearray(96 * 96 * 32)
    for a in font8.ARTS:
        for b in font8.ARTS:
            i = (ord(a) - 0x20) * 0x60 + ord(b) - 0x20
            out[i * 32:i * 32 + 32] = font8.tile_bytes(font8.pair_pixels(a, b))
    return bytes(out)


def lines_of(text):
    return text.split('/')


def plain_len(line):
    return len(TOKEN_EN.sub('', line))


def encode_en(text, budget, width, nlines, enc, pairs=None, cond_chars=None):
    """English -> codes (no terminator). Normal 8 px tiles when every line fits `width` tiles and the total fits
    `budget` codes; otherwise condensed pairs (2 chars per tile). Returns (codes, mode) or raises ValueError."""
    ls = lines_of(text)
    if len(ls) > nlines:
        raise ValueError(f'{len(ls)} lines (max {nlines})')
    bad = sorted({c for c in TOKEN_EN.sub('', text).replace('/', '') if c not in ASCII})
    if bad:
        raise ValueError(f'no tile for {bad}')

    def normal():
        out = []
        for n, line in enumerate(ls):
            if n:
                out.append(NL)
            for part in TOKEN_EN.split(line):
                if TOKEN_EN.fullmatch(part):
                    out.append(0x200 + int(part[5:-1], 16))
                else:
                    out += [enc[ASCII[c]] for c in part]
        return out

    def condensed():
        out = []
        for n, line in enumerate(ls):
            if n:
                out.append(NL)
            for part in TOKEN_EN.split(line):
                if TOKEN_EN.fullmatch(part):
                    out.append(0x200 + int(part[5:-1], 16))
                    continue
                if len(part) % 2:
                    part += ' '
                for i in range(0, len(part), 2):
                    p = part[i:i + 2]
                    if cond_chars is not None and not set(p) <= cond_chars:
                        raise ValueError(f'no condensed glyph for {p!r}')
                    out.append(pair_code(p))
        return out

    codes = normal()
    if len(codes) <= budget and all(plain_len(l) <= width for l in ls):
        return codes, 'normal'
    codes = condensed()
    if len(codes) <= budget and all(-(-plain_len(l) // 2) <= width for l in ls):
        return codes, 'condensed'
    need = max(-(-plain_len(l) // 2) for l in ls)
    raise ValueError(f'too long even condensed: {len(codes)}/{budget} codes, widest line {need}/{width} tiles')


def limits(e):
    """(budget codes, line width tiles, lines) for an entry: in place, JP geometry; 'reloc': N = moved label."""
    if e.get('reloc'):
        return e['reloc'], e['reloc'], 1
    ls = lines_of(e['jp'])
    return e['len'], max(plain_len(TOKEN.sub('x', l)) for l in ls), len(ls)


SPACE = 0x01  # fullwidth-space tile


STRNCPY16 = 0x080365DC   # copy until 0 or max: pieces copied by it are padded with 0, so composed messages close up


def strncpy_targets(rom, code_end=0x0A0000):
    """String offsets loaded from a Thumb literal pool and passed to strncpy16 within the next 8 instructions."""
    lit_users = {}
    for a in range(0, code_end, 2):
        h = struct.unpack_from('<H', rom, a)[0]
        if h >> 11 == 0b01001:
            lit_users.setdefault(((a + 4) & ~3) + (h & 0xFF) * 4, []).append(a)
    out = set()
    for lit, users in lit_users.items():
        v = struct.unpack_from('<I', rom, lit)[0] - romlib.BASE
        if not 0 <= v < len(rom):
            continue
        for a in users:
            for b in range(a + 2, a + 18, 2):
                hi, lo = struct.unpack_from('<HH', rom, b)
                if hi >> 11 == 0b11110 and lo >> 11 == 0b11111:
                    off = ((hi & 0x7FF) << 12 | (lo & 0x7FF) << 1)
                    if off & 0x400000:
                        off -= 0x800000
                    if 0x08000000 + b + 4 + off == STRNCPY16:
                        out.add(v)
                    break
    return out


def build(rom, marker=False, free=None):
    """Write translated 8x8 strings in place; -> (strings written, cache pool, codes still used by Japanese).
    The caller assembles asm/menu8.asm with pairs_bin() and the pool (FREE_CODES minus codes Japanese still uses)."""
    import font8
    dec, enc = romlib.load_table('jp8')
    pairs = None
    cond_chars = set(font8.ARTS)
    jp_used = set()
    zero_pad = strncpy_targets(romlib.rom_bytes())
    n = 0
    for bank in BANKS:
        path = romlib.ROOT / 'script' / f'm8_{bank}.json'
        if not path.exists():
            continue
        for e in json.loads(path.read_text(encoding='utf-8')):
            text = e['en'] or (marker_text(e) if marker and e['slots'] else '')
            if not text or e['status'] in ('keep', 'unused', 'data', 'special'):
                if e['status'] not in ('data', 'special'):  # special: written by insert.default_names
                    jp_used.update(encode(e['jp'], enc) if '[' not in e['jp'] else [])
                continue
            budget, width, nl = limits(e)
            try:
                codes, _ = encode_en(text, budget, width, nl, enc, pairs, cond_chars)
            except ValueError as err:
                raise SystemExit(f'm8_{bank} {e["id"]}: {err}')
            if e.get('reloc'):
                # label from a (pointer, u16 length) table: moved to free space, every slot + length repointed
                off = free.put(struct.pack('<%dH' % (len(codes) + 1), *codes, 0), 2)
                for s in e['slots']:
                    s = int(s, 16)
                    struct.pack_into('<I', rom, s, romlib.BASE + off)
                    struct.pack_into('<H', rom, s + 4, len(codes))
                n += 1
                continue
            pad = [0] if e['term'] or int(e['id'], 16) in zero_pad else []
            codes += (pad + [SPACE] * budget)[:budget - len(codes)]
            off = int(e['id'], 16)
            struct.pack_into('<%dH' % budget, rom, off, *codes)
            n += 1
    pool = [c for c in FREE_CODES if c not in jp_used]
    return n, pool, sorted(jp_used & set(FREE_CODES))


def marker_text(e):
    """Short id marker that fits the entry in place (condensed): last 4 hex digits of the id."""
    budget, width, nl = limits(e)
    return e['id'][-4:][:2 * min(budget, width)]


def walk(rom, start, end, targets):
    """-> (offset, codes, terminated) pieces between 0s and pointer targets; runs of 0 are skipped."""
    off = start
    while off < end:
        if struct.unpack_from('<H', rom, off)[0] == 0 and off not in targets:
            off += 2
            continue
        codes, o = [], off
        while o < end:
            c = struct.unpack_from('<H', rom, o)[0]
            if c == 0 or (o != off and o in targets):
                break
            codes.append(c)
            o += 2
        term = o < end and struct.unpack_from('<H', rom, o)[0] == 0
        yield off, codes, term
        off = o + (2 if term else 0)


def dump(report=False):
    rom = romlib.rom_bytes()
    dec, _ = romlib.load_table('jp8')
    slots = romlib.pointer_slots(rom)
    for bank, ranges in BANKS.items():
        entries = []
        for start, end in ranges:
            targets = {t for t in slots if start <= t < end}
            for off, codes, term in walk(rom, start, end, targets):
                entries.append({'id': '%06X' % off, 'slots': ['%06X' % s for s in slots.get(off, [])],
                                'jp': decode(codes, dec), 'len': len(codes), 'term': term})
        path = romlib.ROOT / 'script' / f'm8_{bank}.json'
        old = {e['id']: e for e in json.loads(path.read_text(encoding='utf-8'))} if path.exists() else {}
        for e in entries:
            o = old.get(e['id'], {})
            e['en'], e['status'] = o.get('en', ''), o.get('status', 'todo')
            if o.get('notes'):
                e['notes'] = o['notes']
        path.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
        if report:
            noref = sum(1 for e in entries if not e['slots'])
            unk = sum(1 for e in entries if '[' in e['jp'])
            packed = sum(1 for e in entries if not e['term'])
            print(f'{bank}: {len(entries)} strings, {noref} unreferenced, {packed} packed, {unk} with unknown codes, '
                  f'{sum(e["len"] for e in entries)} codes')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['dump'])
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    dump(a.report)
