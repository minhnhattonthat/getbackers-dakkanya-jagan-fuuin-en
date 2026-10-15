"""English text encoder for the 12 px dialogue font (digraph scheme).

Every 12 px glyph cell holds TWO 6 px half-width letters (5 px art + 1 px gap). English text is cut into
halves; each distinct pair of halves gets its own glyph code, allocated at build time from the kanji
range 0x100-0x7FF (block 0 = ASCII/kana/digits stays intact: game code prints digits from it).
"  " (two half spaces) is the game's own full-width space 0x5C3. Full-width specials keep block-0 codes.
Line width therefore = ceil(chars / 2) cells."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACE_CODE = 0x5C3
FULL = {'…': 0xAF, '♪': 0x60, '♥': 0xB1, '☆': 0xF0}
FIRST, LAST = 0x100, 0x7FF
Y_OFF = 2          # font_en rows 0-10 -> glyph rows 2-12 (JP glyphs use rows 0-14)
INK = 3


def load_font():
    """char -> list of art rows (strings of . and #), placed at its TOP row."""
    font = {}
    cur = None
    with open(os.path.join(ROOT, 'tbl', 'font_en.txt'), encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('== '):
                parts = line[3:].split()
                ch = parts[0]
                if ch.startswith('U+'):
                    ch = chr(int(ch[2:], 16))
                cur = font[ch] = {'top': int(parts[1]), 'rows': []}
            elif cur is not None and line and set(line) <= set('.#'):
                cur['rows'].append(line)
    return font


FONT = load_font()
HALF = set(FONT) - set(FULL)


def check_text(s):
    """List of characters the encoder cannot draw."""
    return sorted({c for c in s if c not in HALF and c not in FULL and c != '\n'})


def halves(line):
    """Cut one display line into cells: ('pair', a, b) or ('full', code)."""
    cells = []
    pend = None
    for c in line:
        if c in FULL:
            if pend is not None:
                cells.append(('pair', pend, ' '))
                pend = None
            cells.append(('full', FULL[c]))
        elif pend is None:
            pend = c
        else:
            cells.append(('pair', pend, c))
            pend = None
    if pend is not None:
        cells.append(('pair', pend, ' '))
    return cells


def cell_width(line):
    return len(halves(line))


class Encoder:
    """Allocates digraph codes. Call add() for every string first, then freeze(), then encode()."""

    def __init__(self, reserved=()):
        self.pairs = {}
        self.reserved = set(reserved) | {SPACE_CODE}
        self.frozen = False

    def add(self, line):
        for c in halves(line):
            if c[0] == 'pair' and (c[1], c[2]) != (' ', ' '):
                self.pairs.setdefault((c[1], c[2]), None)

    def freeze(self):
        free = [c for c in range(FIRST, LAST + 1) if c not in self.reserved]
        keys = sorted(self.pairs)
        if len(keys) > len(free):
            raise SystemExit('digraph table full: %d pairs, %d codes' % (len(keys), len(free)))
        for k, code in zip(keys, free):
            self.pairs[k] = code
        self.frozen = True

    def encode(self, line):
        assert self.frozen
        out = []
        for c in halves(line):
            if c[0] == 'full':
                out.append(c[1])
            elif (c[1], c[2]) == (' ', ' '):
                out.append(SPACE_CODE)
            else:
                out.append(self.pairs[(c[1], c[2])])
        return out

    def glyphs(self):
        """code -> 16x16 pixel rows for every allocated pair."""
        return {code: render_pair(a, b) for (a, b), code in self.pairs.items()}


def render_pair(a, b):
    px = [[0] * 16 for _ in range(16)]
    for x0, ch in ((0, a), (6, b)):
        g = FONT[ch]
        w = max((len(r.rstrip('.')) for r in g['rows']), default=0)
        x0 += (5 - w) // 2 if w < 4 else 0       # centre narrow letters (i, l, !) in their 6 px cell
        for r, row in enumerate(g['rows']):
            for x, v in enumerate(row):
                if v == '#':
                    px[Y_OFF + g['top'] + r][x0 + x] = INK
    return px


def wrap(text, width_chars):
    """Greedy wrap of a paragraph (explicit \\n kept) into lines of at most width_chars halves."""
    lines = []
    for para in text.split('\n'):
        words = para.split(' ')
        cur = ''
        for w in words:
            cand = w if not cur else cur + ' ' + w
            if line_halves(cand) <= width_chars:
                cur = cand
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def line_halves(line):
    return sum(2 if c in FULL else 1 for c in line)


if __name__ == '__main__':
    e = Encoder()
    for s in ['Hello, Ginji!', 'Ban…']:
        e.add(s)
    e.freeze()
    assert e.encode('Ban…') == [e.pairs[('B', 'a')], e.pairs[('n', ' ')], 0xAF]
    assert e.encode('  ') == [SPACE_CODE]
    assert wrap('one two three', 7) == ['one two', 'three']
    print('enc selftest ok')
