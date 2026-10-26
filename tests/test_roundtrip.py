import json
import unittest

from tools import romlib, dump, menu8


@unittest.skipUnless(romlib.ROM.exists(), 'needs rom/mg_jp.gba')
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

    def test_m8_entries_inside_banks(self):
        # 0x0A1A38 is the port map tile set header right after the msg bank: writing it broke the port (issue #1)
        self.assertLessEqual(menu8.BANKS['msg'][-1][1], 0x0A1A38)
        for bank, ranges in menu8.BANKS.items():
            path = romlib.ROOT / 'script' / f'm8_{bank}.json'
            for e in json.loads(path.read_text(encoding='utf-8')):
                off = int(e['id'], 16)
                self.assertTrue(any(s <= off and off + 2 * e['len'] <= t for s, t in ranges), f'm8_{bank} {e["id"]}')


if __name__ == '__main__':
    unittest.main()
