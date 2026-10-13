"""Translator batches: split script banks into TSV batches, check agent output, merge it into script/*.json.

    python -X utf8 tools/batches.py split BANK [--ids FROM-TO] [--chars 3500] [--prefix s]
    python -X utf8 tools/batches.py check BATCH       # validates work/tl/BATCH.out.tsv, prints OK or errors
    python -X utf8 tools/batches.py merge BATCH       # check, then write English into script/<bank>.json

Input  work/tl/<batch>.tsv      id<TAB>form<TAB>limit<TAB>jp
Output work/tl/<batch>.out.tsv  id<TAB>en
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import insert  # noqa: E402
import menu8  # noqa: E402
import romlib  # noqa: E402
import vwf  # noqa: E402

TL = romlib.ROOT / 'work' / 'tl'
CTL = re.compile(r'\{[^}]*\}')
LIMITS = {'story': 'auto-wrapped, 2 lines x 204px per page', 'ui9': '2 lines x 110px (help/info box)'}


def bank_of(batch):
    return json.loads((TL / f'{batch}.meta.json').read_text(encoding='utf-8'))['bank']


def load_bank(bank):
    return json.loads((romlib.ROOT / 'script' / f'{bank}.json').read_text(encoding='utf-8'))


def save_bank(bank, entries):
    (romlib.ROOT / 'script' / f'{bank}.json').write_text(
        json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def controls(text):
    """Control multiset that must survive translation ({br} is layout; {name} may be repeated or dropped freely)."""
    return Counter(c for c in CTL.findall(text) if c not in ('{br}', '{name}'))


def split(bank, ids=None, chars=3500, prefix=None):
    TL.mkdir(parents=True, exist_ok=True)
    # 8x8 packed strings are often reached by base+offset, so unreferenced ones are translated too
    todo = [e for e in load_bank(bank) if (e['slots'] or bank.startswith('m8_'))
            and e['status'] == 'todo' and not e['en']]
    if ids:
        lo, hi = (int(x, 16) for x in ids.split('-'))
        todo = [e for e in todo if lo <= int(e['id'], 16) <= hi]
    batches, cur, n = [], [], 0
    for e in todo:
        if cur and n + len(e['jp']) > chars:
            batches.append(cur); cur, n = [], 0
        cur.append(e); n += len(e['jp'])
    if cur:
        batches.append(cur)
    prefix = prefix or bank
    existing = len(list(TL.glob(f'{prefix}*.meta.json')))
    for i, b in enumerate(batches, existing + 1):
        name = f'{prefix}{i:02d}'
        lines = [f"{e['id']}\t{'menu' if bank.startswith('m8_') else 'narration'}\t"
                 f"{m8_limit(e) if bank.startswith('m8_') else LIMITS[bank]}\t{e['jp']}" for e in b]
        (TL / f'{name}.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
        (TL / f'{name}.meta.json').write_text(json.dumps({'bank': bank, 'ids': [e['id'] for e in b]}),
                                              encoding='utf-8', newline='\n')
        print(name, len(b), 'entries', sum(len(e['jp']) for e in b), 'jp chars')


def read_out(batch):
    path = TL / f'{batch}.out.tsv'
    out, errs = {}, []
    for n, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if not line.strip():
            continue
        if '\t' not in line:
            errs.append(f'line {n}: no TAB'); continue
        i, en = line.split('\t', 1)
        if i in out:
            errs.append(f'{i}: duplicate id')
        out[i] = en
    return out, errs


def check_m8(e, en):
    """8x8 menu text: ASCII, same palette codes, fits in place (normal or condensed)."""
    errs = []
    if '\t' in en or '\\u' in en:
        errs.append('tab or \\u escape')
    bad = sorted({c for c in en if ord(c) > 0x7E or ord(c) < 0x20})
    if bad:
        errs.append(f'non-ASCII {bad}')
    if controls(e['jp']) != controls(en):
        errs.append(f'controls differ: jp {sorted(controls(e["jp"]).elements())} en {sorted(controls(en).elements())}')
    _, enc = romlib.load_table('jp8')
    import font8
    try:
        menu8.encode_en(en, *menu8.limits(e), enc, None, set(font8.ARTS))
    except ValueError as err:
        errs.append(str(err))
    return errs


def m8_limit(e):
    budget, width, nl = menu8.limits(e)
    return f'{nl} line(s) x {width} tiles, {budget} tiles total (1 char/tile normal, 2 chars/tile condensed)'


def check_entry(bank, jp, en, font):
    if bank.startswith('m8_'):
        return check_m8(jp, en)  # jp is the whole entry for 8x8 banks
    errs = []
    if '\t' in en or '\\u' in en:
        errs.append('tab or \\u escape')
    bad = sorted({c for c in en if ord(c) > 0x7E or ord(c) < 0x20})
    if bad:
        errs.append(f'non-ASCII {bad}')
    if controls(jp) != controls(en):
        errs.append(f'controls differ: jp {sorted(controls(jp).elements())} en {sorted(controls(en).elements())}')
    miss = font.missing(CTL.sub('', en))
    if miss:
        errs.append(f'no glyph for {miss}')
    if re.search(r'\{(name|word1:[0-9A-F]+|word2:[0-9A-F]+)\}(st|nd|rd|th)\b', en):
        errs.append('ordinal suffix glued to a variable')
    if bank == 'ui9':
        cfg = insert.BANKS[bank]
        toks = insert.layout(en, font, cfg['width'], 99, 72)
        nlines = 1 + sum(1 for k, v in toks if v == '{br}')
        if nlines > cfg['lines']:
            errs.append(f'{nlines} lines at {cfg["width"]}px (max {cfg["lines"]})')
    return errs


def vfont(bank):
    return None if bank.startswith('m8_') else vwf.Font(insert.BANKS[bank]['font'])


def check(batch, quiet=False):
    bank = bank_of(batch)
    meta = json.loads((TL / f'{batch}.meta.json').read_text(encoding='utf-8'))
    jp = {e['id']: (e if bank.startswith('m8_') else e['jp']) for e in load_bank(bank)}
    font = vfont(bank)
    out, errs = read_out(batch)
    want = set(meta['ids'])
    for i in sorted(want - set(out)):
        errs.append(f'{i}: missing')
    for i in sorted(set(out) - want):
        errs.append(f'{i}: not in batch')
    for i, en in out.items():
        if i in want:
            errs += [f'{i}: {m}' for m in check_entry(bank, jp[i], en, font)]
    if not quiet:
        print('\n'.join(errs) if errs else 'OK')
    return out, errs


def merge(batch):
    out, errs = check(batch, quiet=True)
    if errs:
        print('\n'.join(errs)); sys.exit('merge refused')
    bank = bank_of(batch)
    entries = load_bank(bank)
    n = 0
    for e in entries:
        if e['id'] in out:
            e['en'], e['status'] = out[e['id']], 'done'
            n += 1
    save_bank(bank, entries)
    print(f'merged {n} entries into script/{bank}.json')


def fix(bank, path):
    """Apply reviewed replacements (id<TAB>en lines) to one bank, with the same per-entry checks."""
    entries = load_bank(bank)
    by_id = {e['id']: e for e in entries}
    font = vfont(bank)
    errs, rows = [], {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            i, en = line.split('\t', 1)
            if i not in by_id:
                errs.append(f'{i}: unknown id')
                continue
            src = by_id[i] if bank.startswith('m8_') else by_id[i]['jp']
            errs += [f'{i}: {m}' for m in check_entry(bank, src, en, font)]
            rows[i] = en
    if errs:
        print('\n'.join(errs)); sys.exit('fix refused')
    for i, en in rows.items():
        by_id[i]['en'], by_id[i]['status'] = en, 'done'
    save_bank(bank, entries)
    print(f'fixed {len(rows)} entries in script/{bank}.json')


if __name__ == '__main__':
    if sys.argv[1:2] == ['fix']:
        fix(sys.argv[2], sys.argv[3])
        sys.exit()
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['split', 'check', 'merge'])
    ap.add_argument('target')
    ap.add_argument('--ids')
    ap.add_argument('--chars', type=int, default=3500)
    ap.add_argument('--prefix')
    a = ap.parse_args()
    if a.cmd == 'split':
        split(a.target, a.ids, a.chars, a.prefix)
    elif a.cmd == 'check':
        sys.exit(1 if check(a.target)[1] else 0)
    else:
        merge(a.target)
