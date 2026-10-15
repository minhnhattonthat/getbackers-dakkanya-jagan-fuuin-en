"""Graphics text: redraw Japanese drawn as tiles (docs/re/graphics.md).

Each job edits a raw 8bpp/4bpp tile block in the ROM through a BG map taken from a VRAM dump: the map tells which
tile sits where on screen, the job paints English into screen rectangles (palette indices), and the changed tiles
are written back to their ROM offsets. Tiles shared with an unedited area are refused.
  python -X utf8 tools/gfx.py show JOB      -> work/gfx_<job>.png (the composed layer, 4x, with a grid)
  build.py calls apply(rom) for every job in JOBS."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMPS = os.path.join(ROOT, 'tbl', 'gfx')     # committed VRAM/palette dumps the jobs are based on

# micro font 3x5 (rows top to bottom) for very small labels
MICRO = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'N': ['#.#', '###', '###', '###', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'],
}


def draw_micro(img, x, y, text, ink):
    for i, ch in enumerate(text):
        for r, row in enumerate(MICRO[ch]):
            for c, v in enumerate(row):
                if v == '#':
                    img[y + r][x + i * 4 + c] = ink


def font_rows(ch):
    g = enc.FONT[ch]
    return g['top'], g['rows']


class Layer:
    def __init__(self, vram, mapat, tilesat, bpp, rom_tiles, tile0):
        self.vram, self.mapat, self.tilesat, self.bpp = vram, mapat, tilesat, bpp
        self.rom_tiles, self.tile0 = rom_tiles, tile0     # ROM offset of tile index tile0
        self.tsize = 64 if bpp == 8 else 32

    def entry(self, cx, cy):
        e = struct.unpack_from('<H', self.vram, self.mapat + 2 * (cy * 32 + cx))[0]
        return e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, e >> 12

    def tile_px(self, t):
        o = self.tilesat + t * self.tsize
        d = self.vram[o:o + self.tsize]
        if self.bpp == 8:
            return [list(d[r * 8:r * 8 + 8]) for r in range(8)]
        return [[(d[r * 4 + c // 2] >> (4 * (c & 1))) & 15 for c in range(8)] for r in range(8)]


def compose(layer):
    img = [[0] * 256 for _ in range(256)]
    for cy in range(32):
        for cx in range(32):
            t, hf, vf, pal = layer.entry(cx, cy)
            px = layer.tile_px(t)
            for r in range(8):
                for c in range(8):
                    v = px[7 - r if vf else r][7 - c if hf else c]
                    if layer.bpp == 4 and v:
                        v |= pal << 4
                    img[cy * 8 + r][cx * 8 + c] = v
    return img


def draw_text(img, x, y, text, ink, outline=None, adv=6):
    """font_en text, top-left at (x, y) = top of the cap rows; outline = 1 px border colour."""
    pts = set()
    for i, ch in enumerate(text):
        if ch == ' ':
            continue
        top, rows = font_rows(ch)
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == '#':
                    pts.add((x + i * adv + c, y + top - 1 + r))
    if outline is not None:
        for (px, py) in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (px + dx, py + dy)
                    if q not in pts and 0 <= q[0] < 256 and 0 <= q[1] < 256:
                        img[q[1]][q[0]] = outline
    for (px, py) in pts:
        img[py][px] = ink


def text_width(text, adv=6):
    return len(text) * adv - 1


def write_back(layer, img, rect, rom, orig_img):
    """Write the tiles covering rect (x0,y0,x1,y1, map space) back to ROM. Returns changed tile count."""
    x0, y0, x1, y1 = rect
    owners = {}
    for cy in range(32):
        for cx in range(32):
            t, hf, vf, pal = layer.entry(cx, cy)
            owners.setdefault(t, []).append((cx, cy, hf, vf))
    done = set()
    n = 0
    for cy in range(y0 // 8, (y1 + 7) // 8):
        for cx in range(x0 // 8, (x1 + 7) // 8):
            t, hf, vf, pal = layer.entry(cx, cy)
            if t in done:
                continue
            new = [[img[cy * 8 + (7 - r if vf else r)][cx * 8 + (7 - c if hf else c)] for c in range(8)]
                   for r in range(8)]
            old = [[orig_img[cy * 8 + (7 - r if vf else r)][cx * 8 + (7 - c if hf else c)] for c in range(8)]
                   for r in range(8)]
            if new == old:
                continue
            others = [o for o in owners[t] if not (o[0] == cx and o[1] == cy)]
            if others:
                raise SystemExit('tile %d at %d,%d is also used at %s' % (t, cx, cy, others[:3]))
            off = layer.rom_tiles + (t - layer.tile0) * layer.tsize
            if layer.bpp == 8:
                data = bytes(v for row in new for v in row)
            else:
                data = bytes((row[c] & 15) | ((row[c + 1] & 15) << 4) for row in new for c in range(0, 8, 2))
            rom[off:off + layer.tsize] = data
            done.add(t)
            n += 1
    return n


def fill(img, rect, colour):
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            img[y][x] = colour


def load_dump(name):
    p = os.path.join(DUMPS, name)
    return open(p + '.vram.bin', 'rb').read(), open(p + '.pal.bin', 'rb').read()


def title_job(rom):
    vram, pal = load_dump('title')
    lay = Layer(vram, 0x1000, 0x8000, 8, 0x8505C, 2)
    img = compose(lay)
    orig = [row[:] for row in img]
    edits = []
    for e in TITLE_EDITS:
        fill(img, e['rect'], e['bg'])
        x0, y0, x1, y1 = e['rect']
        if e.get('micro'):
            w = 4 * len(e['text']) - 1
            draw_micro(img, x0 + (x1 - x0 - w) // 2, y0 + e.get('dy', 2), e['text'], e['ink'])
        else:
            w = text_width(e['text'], e.get('adv', 6))
            draw_text(img, x0 + (x1 - x0 - w) // 2, y0 + e.get('dy', 2), e['text'], e['ink'], e.get('outline'),
                      e.get('adv', 6))
        edits.append(e['rect'])
    n = 0
    for r in edits:
        n += write_back(lay, img, r, rom, orig)
    return n


# title logo (BG2, 8bpp tiles at ROM 0x8505C): 奪還屋 box and the 邪眼封印！ diamond strip
TITLE_EDITS = [
    {'rect': (176, 71, 216, 83), 'bg': 220, 'ink': 151, 'text': 'DAKKANYA', 'micro': True, 'dy': 4},
    {'rect': (93, 92, 200, 106), 'bg': 151, 'ink': 239, 'outline': 101, 'text': 'EVIL EYE SEALED!', 'dy': 3},
]
def title_copyright(rom):
    """Copyright line under the title menu: OBJ strip y 136, 7 sprites 32x16 + one 16x16, tiles 60-119 (1D),
    raw 4bpp at ROM 0x1B51A8 (tile 60). Ink 1 (white), outline 4 (black)."""
    w, h = 240, 16
    img = [[0] * w for _ in range(h)]
    text = '(C)Aoki/Ayamine/Kodansha/Team Dakkanya'
    canvas = [[0] * 256 for _ in range(256)]
    draw_text(canvas, (w - text_width(text)) // 2, 4, text, 1, 4)
    for y in range(h):
        img[y] = canvas[y][:w]
    base = 0x1B51A8
    n = 0
    for k in range(8):
        tw = 4 if k < 7 else 2
        t0 = 60 + 8 * k
        for ty in range(2):
            for tx in range(tw):
                t = t0 + ty * tw + tx
                data = bytearray(32)
                for r in range(8):
                    for c in range(0, 8, 2):
                        x = 32 * k + tx * 8 + c
                        a, b = img[ty * 8 + r][x], img[ty * 8 + r][x + 1]
                        data[r * 4 + c // 2] = a | (b << 4)
                off = base + (t - 60) * 32
                rom[off:off + 32] = data
                n += 1
    return n


JOBS = {'title': title_job, 'title_copyright': title_copyright}


def apply(rom):
    total = 0
    for name, job in JOBS.items():
        if os.path.exists(os.path.join(DUMPS, name.split('_')[0] + '.vram.bin')):
            total += job(rom)
    return total


def show(name):
    from PIL import Image
    vram, pal = load_dump(name)
    lay = Layer(vram, 0x1000, 0x8000, 8, 0x8505C, 2)
    img = compose(lay)
    cols = [struct.unpack_from('<H', pal, 2 * i)[0] for i in range(256)]
    rgb = [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in cols]
    im = Image.new('RGB', (256, 256))
    im.putdata([rgb[v] for row in img for v in row])
    im = im.resize((1024, 1024), Image.NEAREST)
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    for i in range(0, 1024, 32):
        d.line([(i, 0), (i, 1023)], fill=(60, 60, 60))
        d.line([(0, i), (1023, i)], fill=(60, 60, 60))
    im.save(os.path.join(ROOT, 'work', 'gfx_%s.png' % name))
    return img


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'show':
        show(sys.argv[2])
    else:
        print(__doc__)
