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
