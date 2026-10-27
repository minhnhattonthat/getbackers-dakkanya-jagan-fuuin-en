"""Box layout per text kind: limits (in 6 px halves) and how English becomes script records.
Limits are the measured width gate (docs/re/windows.md)."""
import re

import enc

# kind -> (halves per line, lines per page); msg pages beyond the first become extra boxes
LIMITS = {
    'msg': (36, 2),      # measured: 18 cells per line, page arrow in cell 19 of line 2
    'prompt': (36, 1),
    'choice': (34, 1),   # window widened by choice_cmd (screen = 30 tiles; text starts 2 tiles in)
    'bline': (36, 1),    # battle cut-in box = 18 cells (marker battle, bank lines shown at full width)
    'name': (12, 1),     # measured: name tag shows 6 cells
    'bname': (24, 1),
    'bank': (36, 1),
}
OP_MSG1, OP_MSG2 = 0x8000000A, 0x8000000B
SENTENCE_END = ('.', '!', '?', '…', '~', '♥', '♪')


TITLES = ('Mr.', 'Mrs.', 'Ms.', 'Dr.')


def _even(text, w):
    """Wrap at the narrowest width that keeps the line count, so lines even out (no one-word last line), unless
    that leaves a title ("Mr.") at a line end apart from its name."""
    lines = enc.wrap(text, w)
    if len(lines) > 1:
        for w2 in range(w // 2, w + 1):  # 2+ lines means > w halves of text, so no even split is narrower than w/2
            cand = enc.wrap(text, w2)
            if len(cand) <= len(lines) and max(enc.line_halves(x) for x in cand) <= w2 \
                    and not any(x.endswith(TITLES) for x in cand[:-1]):
                return cand
    return lines


def _line_pages(text, w, n):
    lines = _even(text, w)
    return [lines[i:i + n] for i in range(0, len(lines), n)]


def pages(kind, en):
    """Wrap into pages of n lines, evened out. A message longer than a page is packed a whole sentence at a time
    (each page evened on its own), so pages end on a sentence end, unless that would take more pages."""
    w, n = LIMITS[kind]
    flat = _line_pages(en, w, n)
    if len(flat) < 2:
        return flat
    sents = re.split(r'(?:(?<=[.!?…~♥♪])|(?<=[.!?…~♥♪][)"\']))(?<![A-Z][a-z]\.)(?<!Mr\.) (?=\S)', en)
    out, i = [], 0
    while i < len(sents):
        if len(enc.wrap(sents[i], w)) > n:   # a sentence longer than a page: lay out the rest line by line
            out += _line_pages(' '.join(sents[i:]), w, n)
            break
        j = i + 1
        while j < len(sents) and len(enc.wrap(' '.join(sents[i:j + 1]), w)) <= n:
            j += 1
        out.append(_even(' '.join(sents[i:j]), w))
        i = j
    return out if len(out) <= len(flat) else flat


def emit(u, en):
    """-> (record indices to replace, [('cmd', (op, ...)) | ('txt', line)])."""
    kind = u['kind']
    if kind == 'msg':
        out = []
        for pg in pages('msg', en):
            out.append(('cmd', (OP_MSG1 if len(pg) == 1 else OP_MSG2,)))
            out += [('txt', ln) for ln in pg]
        return [u['recs'][0] - 1] + u['recs'], out
    lines = en.split('\n')
    if len(lines) < len(u['recs']):
        lines += [''] * (len(u['recs']) - len(lines))
    return u['recs'], [('txt', ln) for ln in lines[:len(u['recs'])]]


def choice_cmd(payload, cells):
    """Widen the 8000000C choice window (args: count, x, y, w, h in 8 px tiles) for options `cells` wide.
    Text starts 2 tiles into the window; keep a 1-tile right margin; the screen is 30 tiles wide."""
    import struct
    op, count, x, y, w, h = struct.unpack('<6I', payload)
    need = (cells * 12 + 7) // 8 + 3
    if need > w:
        w = min(need, 30)
        x = min(x, 30 - w)
    return (op, count, x, y, w, h)


RULER ='1234567890123456789012345678901234567890'


FILL = 'The quick brown fox jumps over the lazy dog. ' * 4


def marker(e):
    """Marker text: the entry id, then filler up to the kind's full width (all lines of one page)."""
    w, n = LIMITS[e['kind']]
    tag = e['id']
    if e['kind'] == 'msg':
        return (tag + ' ' + FILL)[:w] + '\n' + FILL[:w]
    return (tag + ' ' + FILL)[:w]


def name_marker(jp):
    return 'NAME' + '-' * 12


if __name__ == '__main__':
    # one page: lines even out instead of a one-word last line
    assert pages('msg', 'Electric catfish... Output: 350 volts') == [['Electric catfish...', 'Output: 350 volts']]
    # two pages: each ends on a sentence end where one exists...
    assert pages('msg', "Well, in this place, I guess it ain't impossible... Bet there's a trick to it, though.") \
        == [["Well, in this place, I guess", "it ain't impossible..."], ["Bet there's a trick to it, though."]]
    # a title stays with its name
    assert not any(ln.endswith(TITLES) for ln in pages('msg', "Let's go... Mr. Transporter, Mr. Protector.")[0])
    # a closing bracket after the sentence end still counts as one
    assert pages('msg', "Shido: (Same thing Juubei said?!) You and Juubei are weirdly alike, y'know.") \
        == [['Shido: (Same thing Juubei said?!)'], ["You and Juubei are", "weirdly alike, y'know."]]
    # ...but never at the cost of an extra page
    long = 'One two three four five six seven. ' * 3
    assert len(pages('msg', long.strip())) == len(_line_pages(long.strip(), *LIMITS['msg']))
    print('layout selftest ok')
