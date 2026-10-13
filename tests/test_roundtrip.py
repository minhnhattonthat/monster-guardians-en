import json
import unittest

from tools import romlib, dump


class RoundtripTest(unittest.TestCase):
    """Every extracted string re-encodes to the original bytes, and the banks cover their ranges gap-free."""

    @classmethod
    def setUpClass(cls):
        cls.rom = romlib.rom_bytes()

    def test_encode_decode_exact(self):
        for bank, (tbl, _, ranges) in dump.BANKS.items():
            dec, enc = romlib.load_table(tbl)
            for start, end in ranges:
                for off, codes in dump.walk(self.rom, start, end):
                    text = romlib.decode(codes[:-1], dec)
                    self.assertNotIn('[', text.replace('[FFFF]', '').replace('[FFFE]', ''), f'{bank} {off:06X} {text}')
                    self.assertEqual(romlib.encode(text, enc) + [romlib.END], codes, f'{bank} {off:06X}')

    def test_ranges_end_on_string_boundary(self):
        for bank, (_, _, ranges) in dump.BANKS.items():
            for start, end in ranges:
                last = None
                for off, codes in dump.walk(self.rom, start, end):
                    last = off + 2 * len(codes)
                self.assertEqual(last, end, f'{bank} range {start:06X}-{end:06X}')

    def test_script_files_match_rom(self):
        for bank in dump.BANKS:
            path = romlib.ROOT / 'script' / f'{bank}.json'
            if not path.exists():
                continue
            dec, enc = romlib.load_table(dump.BANKS[bank][0])
            for e in json.loads(path.read_text(encoding='utf-8')):
                off = int(e['id'], 16)
                self.assertEqual(romlib.encode(e['jp'], enc) + [romlib.END], romlib.read_codes(self.rom, off), e['id'])


if __name__ == '__main__':
    unittest.main()
