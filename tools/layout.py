"""Box layout per text kind: limits (in 6 px halves) and how English becomes script records.
Limits are the measured width gate (docs/re/windows.md)."""
import enc

# kind -> (halves per line, lines per page); msg pages beyond the first become extra boxes
LIMITS = {
    'msg': (36, 2),      # measured: 18 cells per line, page arrow in cell 19 of line 2
    'prompt': (36, 1),
    'choice': (34, 1),   # window widened by choice_cmd (screen = 30 tiles; text starts 2 tiles in)
    'bline': (34, 1),    # provisional until a battle is reached
    'name': (12, 1),     # measured: name tag shows 6 cells
    'bname': (24, 1),
    'bank': (36, 1),
}
OP_MSG1, OP_MSG2 = 0x8000000A, 0x8000000B


def pages(kind, en):
    w, n = LIMITS[kind]
    lines = enc.wrap(en, w)
    return [lines[i:i + n] for i in range(0, len(lines), n)]


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
