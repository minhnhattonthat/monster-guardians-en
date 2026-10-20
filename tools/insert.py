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
import check_rom  # noqa: E402
import gfx  # noqa: E402
import menu8  # noqa: E402
import records  # noqa: E402
import romlib  # noqa: E402
import vwf  # noqa: E402

FREE_START, FREE_END = 0x770000, 0x7A0000   # 0x7A0000-: asm/menu8.asm (see assemble)
# bank -> font size, font struct offset, original glyph count, layout (line px, lines per page)
BANKS = {
    # 17 cells fit, but the page-wait arrow is drawn in the cell after the text: 16 cells like the JP.
    # put-glyph breaks the line itself at the 16th glyph when its line index is 1 (then our page break shows an
    # empty page). After {c7533} the first line on the page already has index 1, so every line is capped at 15.
    'story': dict(font=11, struct=0x0D6C24, nglyphs=685, width=192, lines=2, caps=(15,)),
    # battle popups draw {br} as a glyph and auto-wrap at 11 cells: line breaks become blank-cell padding
    'ui9': dict(font=9, struct=0x0CF520, nglyphs=317, width=110, lines=2, pad=(11, 0x031)),
}
NAME_CHARS = 6            # player name length budget for wrapping ({name} = one OBJ per character)
GRID = 0x0CFB82           # {name}: 8x8 code (name-entry grid index) -> story font glyph code
WORD_TABLES = {'word1': 0x0C7410, 'word2': 0x0C73F0}   # {wordN:i}: string pointers [2i], [2i + 1] (variants)
PAGE = '{clear}'          # control emitted when a page fills up (story: waits for A, then clears)
# Auto-advancing intro: {page} scrolls ONE line up (no wait) and {clear} clears without waiting, so a full page
# gets a timed wait and one {page} per line on screen.
AUTO = (0x0CFF84, 0x0D03E8)
AUTO_WAIT = '{wait:003C}'
# u32 data patches: offset -> (JP value, new value). Scene ops are 5 words [op, a, b, c, d]; op 0x28 sets
# owner var a = b, var 2 = frames per glyph. The intro runs on a timer, so English cells must type faster.
PATCHES = {
    0x0C8D5C: (5, 3),   # intro scene: glyph delay 5 -> 3
    # default hero name レオ (2 codes) -> "Leo" (3): DMA into the save's name field and label lengths
    0x055120: (0x80000002, 0x80000003),
    0x05539C: (0x80000002, 0x80000003),
}
# u16 Thumb instruction patches: offset -> (JP, new)
PATCHES16 = {
    0x0492C4: (0x2202, 0x2203),   # movs r2,#2 -> #3: strncpy16 of the default hero name
    0x049314: (0x2202, 0x2203),
    0x057734: (0x2002, 0x2003),   # hero/heroine select label length
    0x057E1A: (0x2204, 0x2206),   # name copy in bytes
}
# default names: drawn by the 8x8 font AND mapped into the story font by {name}, so normal tiles only
HERO, HEROINE = (0x0BD5A6, 'Leo'), (0x0BD5AA, 'Tina')
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
    """Original glyph array + appended English cells (deduplicated), each with its advance in px (story font:
    asm/story.asm reads the advance table; original glyphs keep the pitch)."""

    def __init__(self, rom, struct_off, n, pitch):
        self.struct = struct_off
        ptr = struct.unpack_from('<I', rom, struct_off + 8)[0] - romlib.BASE
        self.bpg = struct.unpack_from('<I', rom, struct_off + 16)[0]
        self.data = bytearray(rom[ptr:ptr + n * self.bpg])
        self.n, self.index, self.adv = n, {}, bytearray([pitch] * n)

    def code(self, cell, adv=None):
        key = (cell, adv)
        if key not in self.index:
            self.index[key] = self.n + len(self.index)
            self.data += cell
            self.adv.append(self.adv[0] if adv is None else adv)
            if self.index[key] >= 0x7530:
                raise SystemExit('glyph codes ran into the control-code range')
        return self.index[key]

    def commit(self, rom, free):
        off = free.put(bytes(self.data))
        struct.pack_into('<I', rom, self.struct + 8, romlib.BASE + off)
        return free.put(bytes(self.adv)), len(self.adv)


def box_of(bank, e):
    """(width px, lines, pad) for an entry: bank default, or the entry's 'box': [width, lines] (9px boxes wider
    than the 11-cell help box, e.g. the one-line stat help in the monster status screen)."""
    cfg = BANKS[bank]
    if 'box' in e:
        w, n = e['box']
        return w, n, ((w // 10, cfg['pad'][1]) if cfg.get('pad') else None)
    return cfg['width'], cfg['lines'], cfg.get('pad')


def name_glyphs(rom, font, glyphs):
    """{name} maps each 8x8 name code through GRID to a story glyph: point every Latin keyboard code at a
    proportional English glyph (advance = its width) instead of the fullwidth JIS one. -> {name} (px, cells)."""
    dec, _ = romlib.load_table('jp8')
    ascii_of = {v: k for k, v in menu8.ASCII.items()}
    widest = 0
    for k in set(struct.unpack_from('<228H', rom, KEYBOARD + 2 * 456)) | {menu8.SPACE}:
        ch = ascii_of.get(dec.get(k))
        if ch and ch in font.glyphs:
            struct.pack_into('<H', rom, GRID + 2 * k, glyphs.code(font.cells(ch)[0], font.width(ch)))
            widest = max(widest, font.width(ch))
    return NAME_CHARS * widest, NAME_CHARS


def inline_widths(rom, entries, font, name):
    """Controls that print text -> (px, cells): {name}, and {wordN:i} = its widest variant."""
    by_slot = {int(s, 16): e for e in entries for s in e['slots']}
    out = {'{name}': name}
    for ctl, table in WORD_TABLES.items():
        for i in range(0x100):
            variants = [by_slot.get(table + 8 * i + 4 * v) for v in (0, 1)]
            if not all(variants):
                break
            texts = [''.join(v for k, v in parse(e['en'] or '') if k == 'text') for e in variants]
            out['{%s:%04X}' % (ctl, i)] = (max(font.width(t) for t in texts),
                                           max(font.ncells(t) for t in texts))
    return out


def parse(text):
    """-> list of ('text', str) / ('ctl', '{...}')."""
    return [('ctl', p) if TOKEN.fullmatch(p) else ('text', p) for p in TOKEN.split(text) if p]


def words(text):
    """-> (kind, items) list: ('word', [('text', s) / ('ctl', c)...]) split at spaces only, so a control inside a
    word ({colend}.) keeps the punctuation with it; ('break', c) for {br} {clear} {page} {c7533}."""
    out, cur = [], []
    for kind, val in parse(text):
        if kind == 'ctl':
            if val[1:-1].split(':')[0] in ('br', 'clear', 'page', 'c7533'):
                if cur:
                    out.append(('word', cur))
                out.append(('break', val))
                cur = []
            else:
                cur.append((kind, val))
            continue
        for chunk in re.findall(r' +[^ ]*|[^ ]+', val):
            if chunk[0] == ' ' and cur:
                out.append(('word', cur))
                cur = []
            cur.append(('text', chunk))
    if cur:
        out.append(('word', cur))
    return out


def layout(text, font, width, lines, inline, auto=False, abut=False, caps=None, early=frozenset()):
    """English text with controls -> token list of runs ('run', str) and controls ('ctl', '{...}'), with {br} and
    page breaks inserted so that no line exceeds width px and no page exceeds lines.
    inline: control -> (px, cells) for controls that print text ({name}, {word1:N}, {word2:N}).
    abut: the engine advances by each cell's own width (story font, asm/story.asm), so a run continues where the
    previous one ended; else every run starts on a cell boundary.
    caps: max glyph cells per line, by line index on the page.
    auto: intro mode, where {page} scrolls one line: pages end with AUTO_WAIT + one {page} per line shown.
    early: word indices that start a new line (widow control: a page break that would leave one word alone on
    its page is redone one word earlier)."""
    out, cur, x, cells, line = [], '', 0, 0, 0
    opener, count, widows = None, 0, set()   # word that opened the current automatic page, words on it

    def run_px(s):
        return font.width(s) if abut else font.ncells(s) * font.cell

    def cap():
        return caps[min(line, len(caps) - 1)] if caps else 1 << 16

    def fits(items):
        px, n, run = x, cells, cur
        for kind, val in items + [('ctl', '')]:
            if kind == 'text':
                run += val
                continue
            if run:
                px, n, run = px + run_px(run), n + font.ncells(run), ''
            w, c = inline.get(val, (0, 0))
            px, n = px + w, n + c
        return px <= width and n <= cap()

    def flush():
        nonlocal cur, x, cells
        if cur:
            out.append(('run', cur))
            x, cells, cur = x + run_px(cur), cells + font.ncells(cur), ''

    def put(items):
        nonlocal cur, x, cells
        for kind, val in items:
            if kind == 'text':
                cur += val
            else:
                flush()
                out.append((kind, val))
                w, c = inline.get(val, (0, 0))
                x, cells = x + w, cells + c

    def scroll_all():
        out.extend([('ctl', '{page}')] * (line + 1))

    def newline():
        """-> True when it started a new page."""
        nonlocal x, cells, line
        flush()
        x = cells = 0
        if line + 1 >= lines:
            if auto:
                out.append(('ctl', AUTO_WAIT))
                scroll_all()
            else:
                out.append(('ctl', PAGE))
            line = 0
            return True
        out.append(('ctl', '{br}'))
        line += 1
        return False

    def end_page():
        nonlocal opener
        if opener is not None and count == 1:
            widows.add(opener - 1)
        opener = None

    wi = -1
    for kind, val in words(text):
        if kind == 'break':
            name = val[1:-1].split(':')[0]
            if name == 'br':
                if newline():
                    end_page()
                continue
            end_page()
            flush()
            if auto and name == 'page':
                scroll_all()
            else:
                out.append(('ctl', val))
            x, cells, line = 0, 0, 0
            continue
        wi += 1
        if (wi in early or not fits(val)) and (x or cur.strip()):
            if newline():
                end_page()
                opener, count = wi, 0
            first = val[0]
            if first[0] == 'text':
                val = ([('text', first[1].lstrip(' '))] if first[1].strip() else []) + val[1:]
        put(val)
        count += any(v.strip() if k == 'text' else v in inline for k, v in val)
    end_page()
    flush()
    if widows - early:
        return layout(text, font, width, lines, inline, auto, abut, caps, early | widows)
    return out


def encode(tokens, font, glyphs, pad=None, abut=False):
    """pad=(cells per line, blank glyph code): {br} becomes blank cells up to the line end (engine auto-wrap).
    abut: a run's last cell advances only to the run's end."""
    codes, n = [], 0
    for kind, val in tokens:
        if kind == 'run':
            cells = font.cells(val)
            advs = [font.cell] * (len(cells) - 1) + [font.width(val) - font.cell * (len(cells) - 1)]
            cells = [glyphs.code(c, a if abut else None) for c, a in zip(cells, advs)]
            codes += cells
            n += len(cells)
        elif pad and val == '{br}':
            codes += [pad[1]] * (-n % pad[0])
            n = 0
        else:
            codes += romlib.encode(val, {})
            if val in ('{clear}', '{page}'):
                n = 0
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
    for fmt, table in (('<I', PATCHES), ('<H', PATCHES16)):
        for off, (old, new) in table.items():
            if struct.unpack_from(fmt, rom, off)[0] != old:
                raise SystemExit(f'patch {off:06X}: expected {old:#x}')
            struct.pack_into(fmt, rom, off, new)
    default_names(rom, free)
    keyboard(rom)
    qa = qa or {}
    stats, adv = {}, None
    for bank, cfg in BANKS.items():
        path = romlib.ROOT / 'script' / f'{bank}.json'
        font = vwf.Font(cfg['font'])
        glyphs = Glyphs(rom, cfg['struct'], cfg['nglyphs'], font.cell)
        entries = json.loads(path.read_text(encoding='utf-8'))
        abut = bank == 'story'
        inline = inline_widths(rom, entries, font, name_glyphs(rom, font, glyphs)) if abut else {}
        done = 0
        for e in entries:
            if e['status'] == 'unused' or not e['slots']:
                continue
            text = qa.get(e['id']) or e['en'] or (marker_text(e) if marker else '')
            if not text:
                continue
            miss = font.missing(''.join(v for k, v in parse(text) if k == 'text'))
            if miss:
                raise SystemExit(f'{bank} {e["id"]}: no glyph for {miss}')
            auto = bank == 'story' and AUTO[0] <= int(e['id'], 16) < AUTO[1]
            width, lines, pad = box_of(bank, e)
            tokens = layout(text, font, width, lines, inline, auto, abut, cfg.get('caps'))
            if bank == 'ui9' and sum(v == '{clear}' for k, v in tokens) > text.count('{clear}'):
                raise SystemExit(f'ui9 {e["id"]}: more than {lines} line(s) at {width}px')
            codes = encode(tokens, font, glyphs, pad, abut)
            off = free.put(struct.pack('<%dH' % len(codes), *codes), 2)
            for s in e['slots']:
                struct.pack_into('<I', rom, int(s, 16), romlib.BASE + off)
            done += 1
        table = glyphs.commit(rom, free)
        if abut:
            adv = table
        stats[bank] = (done, len(glyphs.index))
    stats['gfx'] = (gfx.apply_all(rom, free), 0)
    n8, pool, kept = menu8.build(rom, marker, free)
    n8 += records.build(rom, lambda t, b, w, n: menu8.encode_en(t, b, w, n, romlib.load_table('jp8')[1], condense=True)[0])
    Path(out_path).parent.mkdir(exist_ok=True)
    Path(out_path).write_bytes(rom)
    assemble(out_path, pool, adv)
    for bank, (n, cells) in stats.items():
        print(f'{bank}: {n} strings, {cells} cells')
    print(f'menu8: {n8} strings/names, cache pool {len(pool)} slots'
          + (f' (kept for Japanese: {", ".join("%X" % c for c in kept)})' if kept else ''))
    print(f'free space used to {free.pos:06X}; wrote {out_path}')


def default_names(rom, free):
    """Leo: relocated (3 codes + 0) and every slot repointed; Tina: in place (4 codes, same as ティーナ)."""
    _, enc = romlib.load_table('jp8')
    leo = [enc[menu8.ASCII[c]] for c in HERO[1]] + [0]
    off = free.put(struct.pack('<%dH' % len(leo), *leo), 2)
    for s in range(0, len(rom) - 3, 4):
        if struct.unpack_from('<I', rom, s)[0] == romlib.BASE + HERO[0]:
            struct.pack_into('<I', rom, s, romlib.BASE + off)
    tina = [enc[menu8.ASCII[c]] for c in HEROINE[1]]
    struct.pack_into('<4H', rom, HEROINE[0], *tina)


KEYBOARD = 0x0BCC44   # name entry: 3 pages x 228 u16 codes (hiragana, katakana, Latin)


def keyboard(rom):
    """Kana tiles are reused by the pair cache and names must stay Latin: every page becomes the Latin page."""
    latin = rom[KEYBOARD + 2 * 456:KEYBOARD + 2 * 684]
    rom[KEYBOARD:KEYBOARD + 2 * 228] = latin
    rom[KEYBOARD + 2 * 228:KEYBOARD + 2 * 456] = latin


ASM_AT = 0x7A0000   # asm/menu8.asm code + pair tiles (296 KB) up to ROM end


def assemble(rom_path, pool, adv):
    """Assemble asm/menu8.asm (+ story.asm) onto the built ROM (armips), with the pair tiles, the cache pool and
    the story font advance table adv = (offset, count)."""
    import subprocess
    work = romlib.ROOT / 'build'
    (work / 'pairs.bin').write_bytes(menu8.pairs_bin())
    (work / 'pool.bin').write_bytes(struct.pack('<%dH' % (len(pool) + 1), len(pool), *pool))
    exe = romlib.ROOT / 'tools' / 'armips' / 'armips.exe'
    cmd = [str(exe), str(romlib.ROOT / 'asm' / 'menu8.asm'),
           '-strequ', 'BUILD_ROM', str(Path(rom_path).resolve()),
           '-strequ', 'POOL_BIN', str(work / 'pool.bin'), '-strequ', 'PAIRS_BIN', str(work / 'pairs.bin'),
           '-equ', 'MENU8_DATA', hex(0x08000000 + ASM_AT),
           '-equ', 'ADV_TABLE', hex(romlib.BASE + adv[0]), '-equ', 'ADV_COUNT', str(adv[1])]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=romlib.ROOT / 'asm')   # .include is cwd-relative
    if r.returncode:
        raise SystemExit('armips failed:\n' + r.stdout + r.stderr)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--marker', action='store_true')
    ap.add_argument('--qa', action='append', default=[], help='ID=TEXT override')
    ap.add_argument('--out', default=str(romlib.ROOT / 'build' / 'mg_en.gba'))
    ap.add_argument('--width', action='append', default=[], help='BANK=PX line width override (measuring)')
    a = ap.parse_args()
    check_rom.check()
    for w in a.width:
        bank, px = w.split('=')
        BANKS[bank]['width'] = int(px)
    build(a.out, a.marker, dict(q.split('=', 1) for q in a.qa))
