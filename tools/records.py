"""Fixed 8-code name fields in data records (8x8 font): monster table and item table.

script/names.json maps each Japanese name to English (<= 16 chars; > 8 chars are drawn condensed, 2 per tile).
Every record whose name matches gets the English, so duplicate records stay consistent.

    python -X utf8 tools/records.py list      # JP names per table, with EN and status
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import romlib  # noqa: E402

# table -> (first record, stride, count, name codes)
TABLES = {
    'monster': (0x0B0A44, 0x34, 234, 8),
    'item': (0x0B5728, 0x40, 42, 8),
}
NAMES = romlib.ROOT / 'script' / 'names.json'


def fields(rom, dec):
    """-> [(table, offset, jp name)]"""
    out = []
    for table, (first, stride, count, n) in TABLES.items():
        for i in range(count):
            off = first + i * stride
            codes = struct.unpack_from('<%dH' % n, rom, off)
            out.append((table, off, ''.join(dec.get(c, '[%04X]' % c) for c in codes if c)))
    return out


def load_names():
    return json.loads(NAMES.read_text(encoding='utf-8')) if NAMES.exists() else {}


REGION = (0x0AE000, 0x0B6B00)   # monster/item/encounter records: names are 8-code fields, zero-padded


def find_fields(orig, enc, names):
    """-> {offset: jp} for every zero-padded 8-code field holding a known name (longest names first; a match
    preceded by a name character is a suffix of a longer name and is skipped)."""
    chars = {enc[c] for jp in names for c in jp}
    found = {}
    for jp in sorted(names, key=len, reverse=True):
        b = struct.pack('<%dH' % len(jp), *[enc[c] for c in jp])
        i = orig.find(b, REGION[0], REGION[1])
        while i >= 0:
            pad = struct.unpack_from('<%dH' % (8 - len(jp)), orig, i + 2 * len(jp)) if len(jp) < 8 else ()
            prev = struct.unpack_from('<H', orig, i - 2)[0]
            if all(x == 0 for x in pad) and prev not in chars and i not in found:
                found[i] = jp
            i = orig.find(b, i + 2, REGION[1])
    return found


def build(rom, encode, width=8):
    """encode(text, budget, width, lines) -> codes. Writes every known name field in place, zero-padded."""
    _, enc = romlib.load_table('jp8')
    names = load_names()
    n = 0
    for off, jp in find_fields(romlib.rom_bytes(), enc, names).items():
        codes = encode(names[jp], width, width, 1)
        codes += [0] * (width - len(codes))
        struct.pack_into('<%dH' % width, rom, off, *codes)
        n += 1
    return n


if __name__ == '__main__':
    dec, _ = romlib.load_table('jp8')
    names = load_names()
    seen = set()
    for table, off, jp in fields(romlib.rom_bytes(), dec):
        if jp not in seen:
            seen.add(jp)
            print(table, f'{off:06X}', jp, '->', names.get(jp, '(todo)'))
