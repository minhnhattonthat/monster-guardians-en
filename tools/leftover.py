"""Text-side leftover check: entries that still have no English (the ROM text is not Shift-JIS, so jp_left.py
cannot scan it). Skips entries marked data / unused / keep / special and unreferenced 11px/9px strings.

    python -X utf8 tools/leftover.py        # exit 1 if anything is left
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JP = re.compile(r'[぀-ヿ一-鿿]')
SKIP = {'data', 'unused', 'keep', 'special'}

left = []
for path in sorted((ROOT / 'script').glob('*.json')):
    if path.name == 'names.json':
        continue
    m8 = path.name.startswith('m8_')
    for e in json.loads(path.read_text(encoding='utf-8')):
        if e['status'] in SKIP or (not m8 and not e['slots']):
            continue
        if not JP.search(e['jp']):
            continue
        if not e['en'] and not (m8 and e['status'] == 'done'):
            left.append(f'{path.stem} {e["id"]} {e["jp"][:30]}')
        elif JP.search(e['en']):
            left.append(f'{path.stem} {e["id"]} Japanese in English: {e["en"][:30]}')
print('\n'.join(left))
print(f'{len(left)} untranslated entries')
sys.exit(1 if left else 0)
