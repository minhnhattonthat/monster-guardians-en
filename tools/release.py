"""Release: gates -> build -> BPS (made, re-applied, verified) -> README -> zip (patch + README only).

    python -X utf8 tools/release.py VERSION        # -> release/Monster_Guardians_EN_vVERSION.zip
Never publishes anything; release/ is gitignored.
"""
import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable, '-X', 'utf8']
SKILL = ROOT / '.claude' / 'skills' / 'translate-retro-game' / 'scripts'

README = """Monster Guardians (GBA) - English translation patch v{version}
================================================================

An unofficial fan translation of Konami's Monster Guardians (Game Boy Advance, 2001, Japan only).
Everything is in English: story, battle prompts, menus, shops, item and monster names, the title
banner, the chapter cards, the battle buttons and the drawn sound effects.

How to apply
------------
Apply Monster_Guardians_EN_v{version}.bps to the original Japanese ROM with any BPS patcher
(Floating IPS, beat, or RomPatcher.js in a browser). No ROM is included or provided.

Required ROM (No-Intro: "Monster Guardians (Japan).gba"):
  Size:    8,388,608 bytes
  CRC32:   93815CDE
  MD5:     a62155a1c3dd4bad9e260a2bf527b69f
  SHA-1:   350351b03349728a8ff0a5b0985ad62df7baacc9

Patched ROM:
  CRC32:   {crc}
  SHA-1:   {sha1}

Notes
-----
- Start a new game. Saves made with the Japanese version keep Japanese names for monsters that
  already exist, and savestates hold the old graphics in video memory.
- Tested in Mesen 2 with a GBA BIOS dump; the game boots, plays the story, menus and battles.
- Menu text that does not fit in its original space uses a compact two-letters-per-tile font,
  drawn by a small engine addition, instead of abbreviations.

Known issues
------------
- The Mobile Adapter / link-cable features (online, link battles, passwords) could not be tested;
  their screens are translated, but password entry may show odd characters.
- Chapters 2 and 3 were checked through the text tools and reviews but not played through in full;
  please report anything odd with a savestate.
- The chapter card glow layer drifts like in the original, so a faint copy of the title can show.

Credits
-------
Translation, engine work and testing: minhnhattonthat, with AI assistance (Claude, Anthropic):
the script was translated and reviewed by AI agents and checked in an emulator; human playtesting
is welcome. Fonts: STIX (SIL Open Font License) for the chapter cards; pixel fonts made for this patch.
Monster Guardians (c) 2001 Konami / Mobile21. This patch is unofficial and not affiliated with Konami.
"""


def run(cmd):
    print('$', ' '.join(str(c) for c in cmd[2:] if c))
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f'release stopped: {cmd[3] if len(cmd) > 3 else cmd}')


def main(version):
    run(PY + [str(ROOT / 'tools' / 'check.py')])
    run(PY + [str(ROOT / 'tools' / 'leftover.py')])
    run(PY + [str(ROOT / 'tools' / 'insert.py')])
    built = ROOT / 'build' / 'mg_en.gba'
    out = ROOT / 'release'
    out.mkdir(exist_ok=True)
    patch = out / f'Monster_Guardians_EN_v{version}.bps'
    run(PY + [str(SKILL / 'bps.py'), 'make', str(ROOT / 'rom' / 'mg_jp.gba'), str(built), str(patch)])
    data = built.read_bytes()
    readme = out / 'README.txt'
    readme.write_text(README.format(version=version, crc='%08X' % (zlib.crc32(data) & 0xFFFFFFFF),
                                    sha1=hashlib.sha1(data).hexdigest()), encoding='utf-8', newline='\r\n')
    z = out / f'Monster_Guardians_EN_v{version}.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(patch, patch.name)
        f.write(readme, 'README.txt')
    print('wrote', z, z.stat().st_size, 'bytes')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
