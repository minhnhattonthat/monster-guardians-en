"""Compare tools/lua/textlog.lua output with the strings in a built ROM: lists strings whose glyphs were not all
drawn (scene ended early, e.g. a timed intro cutting English off). Strings with {name}/{word} are skipped.

    python -X utf8 tools/textcheck.py BUILT.gba work/qa/RUN/log.txt
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import romlib  # noqa: E402

LINE = re.compile(r'f(\d+) src=([0-9A-F]{8}) drawn=(\d+)')
EXPAND = {0x753E, 0x753F, 0x7540}


def expected(rom, off):
    codes, n, i = romlib.read_codes(rom, off), 0, 0
    while i < len(codes) - 1:
        c = codes[i]
        if c in EXPAND:
            return None
        if c in romlib.CTRL:
            i += 1 + romlib.CTRL[c][1]
            continue
        n += 1
        i += 1
    return n


def main(built, log):
    rom = Path(built).read_bytes()
    bad = 0
    for m in LINE.finditer(Path(log).read_text(encoding='utf-8')):
        frame, src, drawn = int(m[1]), int(m[2], 16) - romlib.BASE, int(m[3])
        want = expected(rom, src)
        if want is not None and drawn < want:
            bad += 1
            print(f'f{frame} {src:06X}: drew {drawn}/{want} glyphs')
    print(f'{bad} truncated strings')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(*sys.argv[1:3]) else 0)
