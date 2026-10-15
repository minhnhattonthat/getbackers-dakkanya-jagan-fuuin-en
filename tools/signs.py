"""Shop signs drawn into the field map tile sets (LZ77 blocks; map data table 0x1B34AC.., 7 words per map: size,
palette LZ, tiles LZ, 3 layer maps LZ, 0). A tile set is laid out as a 32-tile-wide sheet; each sign occupies a
rectangle of whole tiles there. The job erases the Japanese (every pixel in the rectangle that is not the sign's
border/background stays) and draws English, then recompresses the tile set into the label area and repoints every
map that uses it.
    python -X utf8 tools/signs.py show TILESPTR X0 Y0 X1 Y1     palette indices of a sheet rectangle (pixels)
    python -X utf8 tools/signs.py sheet OUT.png [--en]           every sign rectangle, before/after (zoom 3)"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lzscan  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, 'rom', 'GetBackers Dakkanya - Jagan Fuuin! (Japan).gba')
TABLE_LO, TABLE_HI = 0x1B34AC, 0x1B4568
SPEC = os.path.join(ROOT, 'tools', 'signs.json')

# 3x5 capitals for small signs (rows top to bottom)
MICRO = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'],
    'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'],
    'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'],
    'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'],
    'J': ['..#', '..#', '..#', '#.#', '.#.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'],
    'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#.#', '###', '###', '#.#', '#.#'],
    'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    'P': ['##.', '#.#', '##.', '#..', '#..'],
    'Q': ['.#.', '#.#', '#.#', '##.', '.##'],
    'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '.##'],
    'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'W': ['#.#', '#.#', '###', '###', '#.#'],
    'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'],
    'Z': ['###', '..#', '.#.', '#..', '###'],
    '0': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['##.', '..#', '.#.', '#..', '###'],
    '3': ['##.', '..#', '.#.', '..#', '##.'],
    '4': ['#.#', '#.#', '###', '..#', '..#'],
    '5': ['###', '#..', '##.', '..#', '##.'],
    '6': ['.##', '#..', '##.', '#.#', '.#.'],
    '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['.#.', '#.#', '.#.', '#.#', '.#.'],
    '9': ['.#.', '#.#', '.##', '..#', '##.'],
    '-': ['...', '...', '###', '...', '...'],
    "'": ['.#.', '.#.', '...', '...', '...'],
    '.': ['...', '...', '...', '...', '.#.'],
    '&': ['.#.', '#.#', '.#.', '#.#', '.##'],
}


def micro_rows(ch):
    return MICRO[ch]


def micro_width(text):
    return sum(2 if c == ' ' else 4 for c in text) - 1


def draw_micro(px, x, y, text, ink):
    for ch in text:
        if ch == ' ':
            x += 2
            continue
        for r, row in enumerate(micro_rows(ch)):
            for c, v in enumerate(row):
                if v == '#':
                    px[y + r][x + c] = ink
        x += 4


def draw_vmicro(px, x, y, text, ink):
    """Micro text turned 90 degrees clockwise: glyph rows become columns (right to left)."""
    for ch in text:
        if ch == ' ':
            y += 2
            continue
        for r, row in enumerate(micro_rows(ch)):
            for c, v in enumerate(row):
                if v == '#':
                    px[y + c][x + 4 - r] = ink
        y += 4


def map_entries(d):
    out = []
    for o in range(TABLE_LO, TABLE_HI, 28):
        out.append(o)
    return out


def load_set(d, tp):
    til = lzscan.lz77(d, tp & 0x1FFFFFF)[0]
    n = len(til) // 32
    rows = (n + 31) // 32
    px = [[0] * 256 for _ in range(rows * 8)]
    for t in range(n):
        for r in range(8):
            for c in range(8):
                b = til[t * 32 + r * 4 + c // 2]
                px[(t // 32) * 8 + r][(t % 32) * 8 + c] = (b >> 4) if c & 1 else b & 15
    return px, n


def store_set(px, n):
    out = bytearray(n * 32)
    for t in range(n):
        for r in range(8):
            for c in range(0, 8, 2):
                y, x = (t // 32) * 8 + r, (t % 32) * 8 + c
                out[t * 32 + r * 4 + c // 2] = px[y][x] | (px[y][x + 1] << 4)
    return bytes(out)


def draw_sign(px, s):
    """s: rect [x0,y0,x1,y1) in sheet pixels, bg (index painted over the old text inside 'clear' or rect),
    ink, lines [[text, x, y, font]] with font 'micro' or 'small' (proportional font_en)."""
    keep = set(s.get('keep', []))
    for key in ('clear', 'clear2'):
        if key not in s and not (key == 'clear' and 'rect' in s):
            continue
        x0, y0, x1, y1 = s[key] if key in s else s['rect']
        for y in range(y0, y1):
            for x in range(x0, x1):
                if px[y][x] not in keep:
                    px[y][x] = s['bg']
    for text, x, y, font in s['lines']:
        layers = ([(1, 1, s['shadow'])] if 'shadow' in s else []) + [(0, 0, s['ink'])]
        for dx, dy, ink in layers:
            if font == 'micro':
                draw_micro(px, x + dx, y + dy, text, ink)
            elif font == 'vmicro':          # rotated 90 degrees clockwise, read top to bottom
                draw_vmicro(px, x + dx, y + dy, text, ink)
            else:
                import captions
                captions.draw(px, x + dx, y + dy, text, ink, None, 1, space=3)


def cells_image(px, cells):
    img = [[0] * (len(cells[0]) * 8) for _ in range(len(cells) * 8)]
    for cy, row in enumerate(cells):
        for cx, e in enumerate(row):
            t, hf, vf = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1
            for r in range(8):
                for c in range(8):
                    rr, cc = (7 - r if vf else r), (7 - c if hf else c)
                    img[cy * 8 + r][cx * 8 + c] = px[(t // 32) * 8 + rr][(t % 32) * 8 + cc]
    return img


def cells_store(px, cells, img):
    """Write a composed sign back into its tiles (through the map entry flips); a tile used by several cells must
    come out the same everywhere."""
    want = {}
    for cy, row in enumerate(cells):
        for cx, e in enumerate(row):
            t, hf, vf = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1
            tile = tuple(tuple(img[cy * 8 + (7 - r if vf else r)][cx * 8 + (7 - c if hf else c)] for c in range(8))
                         for r in range(8))
            assert want.setdefault(t, tile) == tile, 'tile %d is shared by cells that differ' % t
    for t, tile in want.items():
        for r in range(8):
            px[(t // 32) * 8 + r][(t % 32) * 8:(t % 32) * 8 + 8] = list(tile[r])


def draw_any(px, s):
    """Signs given as map cells (signs on scrolling street maps, split across the tile sheet) or as a sheet
    rectangle."""
    if 'cells' in s:
        img = cells_image(px, s['cells'])
        draw_sign(img, s)
        cells_store(px, s['cells'], img)
    else:
        draw_sign(px, s)


def apply(rom, alloc, report=False):
    spec = json.load(open(SPEC, encoding='utf-8'))
    n_done = 0
    for tps, signs in spec.items():
        tp = int(tps, 16)
        px, n = load_set(rom, 0x08000000 + tp)
        for s in signs:
            draw_any(px, s)
        data = __import__('lzcomp').compress(store_set(px, n))
        at = alloc(len(data))
        rom[at:at + len(data)] = data
        users = 0
        for o in map_entries(rom):
            if struct.unpack_from('<I', rom, o + 8)[0] == 0x08000000 + tp:
                struct.pack_into('<I', rom, o + 8, 0x08000000 + at)
                users += 1
        assert users, tps
        n_done += len(signs)
        if report:
            print('signs: tile set %s, %d signs, %d maps' % (tps, len(signs), users))
    return n_done


def show(d, tp, x0, y0, x1, y1):
    px, n = load_set(d, tp)
    for y in range(y0, y1):
        print('%3d ' % y + ''.join('%X' % px[y][x] if px[y][x] else '.' for x in range(x0, x1)))


def sheet(out, en):
    from PIL import Image
    d = bytearray(open(ROM, 'rb').read())
    spec = json.load(open(SPEC, encoding='utf-8'))
    tiles = []
    for tps, signs in spec.items():
        px, n = load_set(d, 0x08000000 + int(tps, 16))
        for s in signs:
            if 'cells' in s:
                img = cells_image(px, s['cells'])
                if en:
                    draw_sign(img, s)
                tiles.append(img)
                continue
            if en:
                draw_sign(px, s)
            x0, y0, x1, y1 = s['rect']
            tiles.append([row[x0:x1] for row in px[y0:y1]])
    Z = 3
    W = max(len(t[0]) for t in tiles) + 2
    H = sum(len(t) + 2 for t in tiles)
    im = Image.new('RGB', (W * Z, H * Z), (255, 0, 255))
    y = 0
    for t in tiles:
        for r, row in enumerate(t):
            for c, v in enumerate(row):
                for a in range(Z):
                    for b in range(Z):
                        im.putpixel((c * Z + b, (y + r) * Z + a), (v * 17,) * 3)
        y += len(t) + 2
    im.save(out)


if __name__ == '__main__':
    if sys.argv[1] == 'show':
        d = open(ROM, 'rb').read()
        show(d, *[int(a, 16) for a in sys.argv[2:3]], *[int(a) for a in sys.argv[3:7]])
    elif sys.argv[1] == 'sheet':
        sheet(sys.argv[2], '--en' in sys.argv)
