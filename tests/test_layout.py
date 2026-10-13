import unittest

from tools import insert, vwf


class LayoutTest(unittest.TestCase):
    def setUp(self):
        self.font = vwf.Font(11)

    def lines(self, tokens):
        """Split runs into display lines (by {br}/page controls) and return (line widths in px, controls)."""
        widths, w, ctls = [], 0, []
        for kind, val in tokens:
            if kind == 'run':
                w += self.font.ncells(val) * self.font.cell
            elif val in ('{br}', '{clear}', '{page}'):
                widths.append(w); w = 0; ctls.append(val)
        widths.append(w)
        return widths, ctls

    def test_wraps_within_width_and_pages(self):
        text = ' '.join(['monster'] * 40)
        tokens = insert.layout(text, self.font, 192, 2, 72)
        widths, ctls = self.lines(tokens)
        self.assertTrue(all(w <= 192 for w in widths), widths)
        self.assertEqual(ctls[:3], ['{br}', '{clear}', '{br}'])
        self.assertNotIn(' ', [v[0] for k, v in tokens if k == 'run'])  # no line starts with a space

    def test_controls_break_runs_and_name_takes_budget(self):
        tokens = insert.layout('Hi {name}, you{wait:003C} came.', self.font, 192, 2, 72)
        kinds = [k for k, _ in tokens]
        self.assertEqual(kinds, ['run', 'ctl', 'run', 'ctl', 'run'])
        long = insert.layout('x' * 20 + ' {name}', self.font, 192, 2, 72)
        self.assertIn(('ctl', '{br}'), long)  # name would overflow: wrapped first

    def test_auto_mode_scrolls_every_line(self):
        two_lines = ' '.join(['monster'] * 8) + '{wait:003C}{page}'
        ctls = [v for k, v in insert.layout(two_lines, self.font, 192, 2, 72, auto=True) if k == 'ctl']
        self.assertEqual(ctls, ['{br}', '{wait:003C}', '{page}', '{page}'])
        three = ' '.join(['monster'] * 12) + '{wait:003C}{page}'
        ctls = [v for k, v in insert.layout(three, self.font, 192, 2, 72, auto=True) if k == 'ctl']
        self.assertEqual(ctls, ['{br}', insert.AUTO_WAIT, '{page}', '{page}', '{wait:003C}', '{page}'])

    def test_encode_roundtrips_controls(self):
        rom = bytearray(64)
        g = insert.Glyphs.__new__(insert.Glyphs)
        g.n, g.index, g.data = 10, {}, bytearray()
        codes = insert.encode([('run', 'ab'), ('ctl', '{col:0002}'), ('ctl', '{name}')], self.font, g)
        self.assertEqual(codes[1:], [0x753B, 2, 0x7540, 0x7FFF])
        self.assertEqual(codes[0], 10)


if __name__ == '__main__':
    unittest.main()
