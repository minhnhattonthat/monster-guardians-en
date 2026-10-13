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


def build(rom, encode, width=8):
    """encode(text, budget, width, lines) -> codes. Writes every known name in place, zero-padded."""
    dec, _ = romlib.load_table('jp8')
    names = load_names()
    n = 0
    for table, off, jp in fields(romlib.rom_bytes(), dec):
        en = names.get(jp)
        if not en:
            continue
        codes = encode(en, width, width, 1)
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
