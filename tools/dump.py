"""Extract u16-code strings from the JP ROM into script/<bank>.json. Never overwrites existing English: an existing
file keeps its 'en'/'status'/'notes' per id; only jp/slots/max metadata is refreshed.

    python -X utf8 tools/dump.py [--report]
"""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import romlib  # noqa: E402

# bank -> (font table, glyph count, [(start, end)] string ranges walked END to END)
BANKS = {
    'ui9': ('jp9', 317, [(0x0CC90E, 0x0CDED4)]),
    'story': ('jp11', 685, [(0x0CF9C4, 0x0CFB82), (0x0CFF84, 0x0D3144)]),
}
# strings inside the ranges that are data, not text (kept out of the script)
DATA = {0x0CC90E: 'ui9 glyph list?'}


def walk(rom, start, end):
    off = start
    while off < end:
        codes = romlib.read_codes(rom, off)
        yield off, codes
        off += 2 * len(codes)


def dump(rom, report=False):
    slots_all = romlib.pointer_slots(rom)
    out = {}
    for bank, (tbl, n, ranges) in BANKS.items():
        dec, _ = romlib.load_table(tbl)
        entries = []
        for start, end in ranges:
            for off, codes in walk(rom, start, end):
                slots = slots_all.get(off, [])
                entries.append({
                    'id': '%06X' % off,
                    'slots': ['%06X' % s for s in slots],
                    'jp': romlib.decode(codes[:-1], dec),
                    'bytes': 2 * len(codes),
                })
        out[bank] = entries
        if report:
            noref = [e for e in entries if not e['slots']]
            print(f'{bank}: {len(entries)} strings, {len(noref)} without pointer')
            for e in noref[:20]:
                print('  noref', e['id'], e['jp'][:40])
    return out


def merge_write(bank, entries):
    path = romlib.ROOT / 'script' / f'{bank}.json'
    old = {}
    if path.exists():
        old = {e['id']: e for e in json.loads(path.read_text(encoding='utf-8'))}
    for e in entries:
        o = old.get(e['id'], {})
        e['en'] = o.get('en', '')
        e['status'] = o.get('status', 'todo')
        for k, v in o.items():   # notes, box, ...: hand-set fields survive a re-dump
            if k not in e:
                e[k] = v
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    rom = romlib.rom_bytes()
    for bank, entries in dump(rom, a.report).items():
        merge_write(bank, entries)
        print(bank, len(entries))
