import unittest

from tools import insert, vwf

NAME = {'{name}': (72, 6)}


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
        tokens = insert.layout(text, self.font, 192, 2, NAME)
        widths, ctls = self.lines(tokens)
        self.assertTrue(all(w <= 192 for w in widths), widths)
        self.assertEqual(ctls[:3], ['{br}', '{clear}', '{br}'])
        self.assertNotIn(' ', [v[0] for k, v in tokens if k == 'run'])  # no line starts with a space

    def test_controls_break_runs_and_name_takes_budget(self):
        tokens = insert.layout('Hi {name}, you{wait:003C} came.', self.font, 192, 2, NAME)
        kinds = [k for k, _ in tokens]
        self.assertEqual(kinds, ['run', 'ctl', 'run', 'ctl', 'run'])
        long = insert.layout('x' * 20 + ' {name}', self.font, 192, 2, NAME)
        self.assertIn(('ctl', '{br}'), long)  # name would overflow: wrapped first

    def test_auto_mode_scrolls_every_line(self):
        two_lines = ' '.join(['monster'] * 8) + '{wait:003C}{page}'
        ctls = [v for k, v in insert.layout(two_lines, self.font, 192, 2, NAME, auto=True) if k == 'ctl']
        self.assertEqual(ctls, ['{br}', '{wait:003C}', '{page}', '{page}'])
        three = ' '.join(['monster'] * 12) + '{wait:003C}{page}'
        ctls = [v for k, v in insert.layout(three, self.font, 192, 2, NAME, auto=True) if k == 'ctl']
        self.assertEqual(ctls, ['{br}', insert.AUTO_WAIT, '{page}', '{page}', '{wait:003C}', '{page}'])

    def test_punctuation_after_control_wraps_with_its_word(self):
        text = 'x' * 22 + ' {col:0002}Lord Bellingham{colend}, the reward'
        tokens = insert.layout(text, self.font, 192, 2, NAME, abut=True)
        line2 = tokens[tokens.index(('ctl', '{br}')) + 1:]
        self.assertEqual(line2[:2], [('run', 'Bellingham'), ('ctl', '{colend}')])
        self.assertEqual(line2[2], ('run', ', the reward'))

    def test_abut_measures_px_and_caps_cells(self):
        # narrow runs split by colour codes: 24 cells in ~110 px, so the cell cap breaks the line, not the width
        tokens = insert.layout(('i {col:0002}i{colend} ' * 12).rstrip(), self.font, 192, 2, NAME, abut=True, caps=(16, 15))
        cells, line = 0, []
        for kind, val in tokens + [('ctl', '{br}')]:
            if kind == 'run':
                cells += self.font.ncells(val)
            elif val in ('{br}', '{clear}'):
                line.append(cells)
                cells = 0
        self.assertEqual(len(line), 2)
        self.assertLessEqual(line[0], 16)
        self.assertEqual(sum(line), 24)

    def test_widow_word_takes_the_previous_word_along(self):
        def pages(text):
            return ''.join(v if k == 'run' else '|' for k, v in insert.layout(text, self.font, 192, 2, NAME, abut=True)
                           if k == 'run' or v == '{clear}').split('|')
        n = 1
        while len(pages('monster ' * (n + 1))) == 1:   # n words fill the page exactly
            n += 1
        self.assertEqual(pages('monster ' * n + 'end.')[-1].split(), ['monster', 'end.'])

    def test_abut_last_cell_advances_to_run_end(self):
        g = insert.Glyphs.__new__(insert.Glyphs)
        g.n, g.index, g.data, g.adv = 10, {}, bytearray(), bytearray([12] * 10)
        run = 'Monster Tamer'
        insert.encode([('run', run)], self.font, g, abut=True)
        w = self.font.width(run)
        self.assertEqual(list(g.adv[10:]), [12] * (w // 12) + [w % 12 or 12])

    def test_pad_replaces_br_with_blank_cells(self):
        g = insert.Glyphs.__new__(insert.Glyphs)
        g.n, g.index, g.data, g.adv = 10, {}, bytearray(), bytearray([12])
        f9 = vwf.Font(9)
        codes = insert.encode([('run', 'ab'), ('ctl', '{br}'), ('run', 'cd')], f9, g, pad=(11, 0x31))
        self.assertEqual(codes.count(0x31), 10)
        self.assertNotIn(0x7530, codes)

    def test_encode_roundtrips_controls(self):
        rom = bytearray(64)
        g = insert.Glyphs.__new__(insert.Glyphs)
        g.n, g.index, g.data, g.adv = 10, {}, bytearray(), bytearray([12])
        codes = insert.encode([('run', 'ab'), ('ctl', '{col:0002}'), ('ctl', '{name}')], self.font, g)
        self.assertEqual(codes[1:], [0x753B, 2, 0x7540, 0x7FFF])
        self.assertEqual(codes[0], 10)


if __name__ == '__main__':
    unittest.main()


class CardWrapTest(unittest.TestCase):
    def test_line_ends_on_word(self):
        from tools import menu8
        s = menu8.card_wrap('Fuse with this equipped to keep its element.', 34)
        self.assertEqual(s[:34].rstrip(), 'Fuse with this equipped to keep')
        self.assertEqual(s[34:], 'its element.')
        self.assertEqual(menu8.card_wrap('Short one.', 34), 'Short one.')