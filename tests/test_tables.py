import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TableTest(unittest.TestCase):
    def test_tables_cover_fonts_without_duplicates(self):
        for name, n in (('jp11', 685), ('jp9', 317)):
            lines = (ROOT / 'tbl' / f'{name}.tbl').read_text(encoding='utf-8').splitlines()
            glyphs = [l.split('=', 1)[1] for l in lines if int(l[2:4] + l[:2], 16) < 0x7530]
            self.assertEqual(len(glyphs), n, name)
            dups = {g for g in glyphs if glyphs.count(g) > 1}
            self.assertEqual(dups, set(), name)


if __name__ == '__main__':
    unittest.main()
