"""Opening demo name captions: BG strips 32x4 tiles (4bpp, one palette), resource entries of 7 words (palette,
palette size, tiles, tiles size, map, map size 0x100, descriptor) in the table around 0xA5FF00.
    python -X utf8 tools/captions.py show OUT.png [--en]
The English job redraws each caption into a fresh tile set (written to free space, entry repointed): the original
picture with the Japanese text area cleared, then the English title and name in an outlined font."""
import struct
import sys

ROM = 'rom/GetBackers Dakkanya - Jagan Fuuin! (Japan).gba'


def entries(d, lo=0xA5FE00, hi=0xA60200):
    out = []
    for o in range(lo, hi, 4):
        pal, psz, t, tsz, m, msz, desc = struct.unpack_from('<7I', d, o)
        if o in (0xA5FED8, 0xA5FEF4, 0xA600D0, 0xA60108) or msz == 0x100 and psz == 0x20 and all(0x08000000 <= x < 0x0A000000 for x in (pal, t, m, desc)) \
                and tsz % 32 == 0 and tsz <= 0x2000:
            out.append(o)
    return out


def compose(d, o):
    pal, psz, t, tsz, m, msz, desc = struct.unpack_from('<7I', d, o)
    t &= 0x1FFFFFF
    m &= 0x1FFFFFF
    rows = msz // 64
    img = [[0] * 256 for _ in range(rows * 8)]
    for cy in range(rows):
        for cx in range(32):
            e = struct.unpack_from('<H', d, m + 2 * (cy * 32 + cx))[0]
            n, hf, vf = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1
            for r in range(8):
                for c in range(8):
                    rr, cc = (7 - r if vf else r), (7 - c if hf else c)
                    b = d[t + n * 32 + rr * 4 + cc // 2]
                    img[cy * 8 + r][cx * 8 + c] = (b >> 4) if cc & 1 else (b & 15)
    cols = [struct.unpack_from('<H', d, (pal & 0x1FFFFFF) + 2 * i)[0] for i in range(16)]
    rgb = [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in cols]
    return img, rgb


# entry -> (title, name); the logo strip (邪眼封印) -> one big line
CAPTIONS = {
    0xA5FF2C: ('The Man with the Evil Eye', 'Ban Mido'),
    0xA5FF48: ('Raitei', 'Ginji Amano'),
    0xA5FF64: ('Lady Poison', 'Himiko Kudo'),
    0xA5FF80: ('Kazuki of the Strings', 'Kazuki Fuchoin'),
    0xA5FF9C: ('Beast Master', 'Shido Fuyuki'),
    0xA5FFB8: ('Bloody Joker', 'Haruki Emishi'),
    0xA60124: ('Juubei of the Flying Needles', 'Juubei Kakei'),
    0xA60140: ('Knight of Hell', 'Toshiki Uryu'),
    0xA6015C: ('Dr. Jackal', 'Kurodo Akabane'),
}
LOGO = (0xA600EC, ('EVIL EYE', 'SEALED'))   # tiles reused by code-built maps: redrawn in place


def glyph(ch):
    import enc
    g = enc.FONT[ch]
    return g['top'], g['rows'], max(len(r) for r in g['rows'])


def text_width(text, s, space=3):
    w = 0
    for ch in text:
        w += space * s if ch == ' ' else (glyph(ch)[2] + 1) * s
    return w - s


def draw(img, x, y, text, ink, outline, s, space=3, sy=None):
    """font_en scaled s times (sy times vertically when given), proportional, with a 1 px outline (None = no
    outline); y = top of the cap rows."""
    pts = set()
    for ch in text:
        if ch == ' ':
            x += space * s
            continue
        top, rows, w = glyph(ch)
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == '#':
                    for dy in range(sy or s):
                        for dx in range(s):
                            pts.add((x + c * s + dx, y + (top - 1 + r) * (sy or s) + dy))
        x += (w + 1) * s
    H, W = len(img), len(img[0])
    if outline is not None:
        for (px, py) in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (px + dx, py + dy)
                    if q not in pts and 0 <= q[0] < W and 0 <= q[1] < H:
                        img[q[1]][q[0]] = outline
    for (px, py) in pts:
        if py < H:          # descenders of the big name may run past the strip
            img[py][px] = ink


def lum(c):
    return c[0] * 3 + c[1] * 6 + c[2]


# the "邪 眼 封印" title card: black 邪 / 封印 on white (BG, A5FED8) around a red 眼 (A5FEF4) that is shown first
# (words with x, y, x scale, y scale); both get a fresh tile set and map
EYE_CARD = {0xA5FED8: (('EVIL', 40, 'SEALED', 122), 64, 2, 4), 0xA5FEF4: (('EYE', 86), 2, 2, 4)}


# title flash: big gold 邪眼封印 (new tiles) and the small white one (unique tiles, redrawn in place)
FLASH = {0xA600D0: (2, 3, 'new'), 0xA60108: (1, 2, 'inplace')}


def english(d, o, img, rgb):
    from collections import Counter
    if o in FLASH:
        sx, sy, _ = FLASH[o]
        cnt = Counter(v for row in img for v in row if v)
        ink = cnt.most_common(1)[0][0]
        rim = max(cnt, key=lambda i: lum(rgb[i]))     # the original strokes have a light rim
        W = max(x for row in img for x, v in enumerate(row) if v) + 1
        new = [[0] * 256 for _ in img]
        text = 'EVIL EYE SEALED'
        w = text_width(text, sx, 2)
        assert w <= W - 4, (w, W)
        draw(new, (W - w) // 2, (len(img) - 8 * sy) // 2, text, ink, rim if sx > 1 else None, sx, space=2, sy=sy)
        return new
    if o in EYE_CARD:
        words, y, sx, sy = EYE_CARD[o]
        cnt = Counter(v for row in img for v in row)
        bg = cnt.most_common(1)[0][0]
        if o == 0xA5FEF4:   # red kanji on its dark field
            ink = max((i for i in cnt if i != bg), key=lambda i: rgb[i][0] - rgb[i][1])
            field = [[bg if v else 0 for v in row] for row in img]
        else:
            ink = min((i for i in cnt), key=lambda i: lum(rgb[i]))
            field = [[bg if 40 <= y0 < 120 and x < 232 and v and v != bg else v for x, v in enumerate(row)]
                     for y0, row in enumerate(img)]       # erase the kanji only
        for k in range(0, len(words), 2):
            draw(field, words[k + 1], y, words[k], ink, None, sx, space=2, sy=sy)
        return field
    if o == LOGO[0]:
        ink = max(range(16), key=lambda i: lum(rgb[i]))
        dark = min((i for i in range(1, 16)), key=lambda i: lum(rgb[i]))
        img = [[0] * 256 for _ in range(32)]
        a, b = LOGO[1]
        assert 18 + text_width(a, 2, 2) <= 150 and 18 + text_width(b, 2, 2) <= 126
        draw(img, 18, 0, a, ink, dark, 2, space=2)
        draw(img, 18, 16, b, ink, dark, 2, space=2)
        return img
    title, name = CAPTIONS[o]
    cnt = Counter(v for row in img for v in row if v)
    bg = cnt.most_common(1)[0][0]
    ink = min((i for i in cnt if i != bg), key=lambda i: abs(lum(rgb[i]) - lum((104, 64, 80))))
    outline = max((i for i in cnt if i != bg), key=lambda i: lum(rgb[i]))
    img = [[bg if v else 0 for v in row] for row in img]
    assert 14 + text_width(title, 1) <= 240 and text_width(name, 2) <= 222, (title, name)
    draw(img, 14, 2, title, ink, outline, 1)
    draw(img, 236 - text_width(name, 2), 13, name, ink, outline, 2)
    return img


def tiles_and_map(img, orig_map):
    """Dedupe 8x8 cells -> (tile bytes, map bytes); map entries keep the original high bits."""
    tiles, index, mp = [], {}, bytearray()
    for cy in range(len(img) // 8):
        for cx in range(32):
            b = bytes(img[cy * 8 + r][cx * 8 + c] | (img[cy * 8 + r][cx * 8 + c + 1] << 4)
                      for r in range(8) for c in range(0, 8, 2))
            if b not in index:
                index[b] = len(tiles)
                tiles.append(b)
            e = struct.unpack_from('<H', orig_map, 2 * (cy * 32 + cx))[0]
            mp += struct.pack('<H', (e & 0xF000) | index[b])
    return b''.join(tiles), bytes(mp)


def apply(rom, alloc):
    n = 0
    for o in entries(rom):
        if o not in CAPTIONS and o != LOGO[0] and o not in EYE_CARD and o not in FLASH:
            continue
        img, rgb = compose(rom, o)
        img = english(rom, o, img, rgb)
        m = struct.unpack_from('<I', rom, o + 16)[0] & 0x1FFFFFF
        if o == LOGO[0] or FLASH.get(o, (0, 0, ''))[2] == 'inplace':   # tiles shared with other maps: in place
            t = struct.unpack_from('<I', rom, o + 8)[0] & 0x1FFFFFF
            msz = struct.unpack_from('<I', rom, o + 20)[0]
            want = {}                 # tile -> the contents every map cell using it asks for
            for cy in range(msz // 64):
                for cx in range(32):
                    e = struct.unpack_from('<H', rom, m + 2 * (cy * 32 + cx))[0]
                    k, hf, vf = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1

                    def px(r, c):        # tile pixel (r, c) = screen pixel through the map entry's flips
                        return img[cy * 8 + (7 - r if vf else r)][cx * 8 + (7 - c if hf else c)]
                    want.setdefault(k, set()).add(bytes(px(r, c) | (px(r, c + 1) << 4)
                                                        for r in range(8) for c in range(0, 8, 2)))
            for k, cells in want.items():
                if len(cells) == 1:
                    rom[t + 32 * k:t + 32 * k + 32] = cells.pop()
                else:
                    print('captions: %X tile %d is shared by cells that differ now, left unchanged' % (o, k))
            n += 1
            continue
        msz = struct.unpack_from('<I', rom, o + 20)[0]
        tl, mp = tiles_and_map(img, rom[m:m + msz])
        assert len(tl) // 32 <= 512, o
        ta = alloc(len(tl))
        rom[ta:ta + len(tl)] = tl
        ma = alloc(len(mp))
        rom[ma:ma + len(mp)] = mp
        struct.pack_into('<II', rom, o + 8, 0x08000000 + ta, len(tl))
        struct.pack_into('<I', rom, o + 16, 0x08000000 + ma)
        n += 1
    return n


def show(d, out, Z=2):
    from PIL import Image, ImageDraw
    es = entries(d)
    imgs = [compose(d, o) for o in es]
    im = Image.new('RGB', (256 * Z, sum(len(i) + 12 for i, _ in imgs) * Z))
    dr = ImageDraw.Draw(im)
    y0 = 0
    for o, (img, rgb) in zip(es, imgs):
        small = Image.new('RGB', (256, len(img)))
        small.putdata([rgb[v] for row in img for v in row])
        im.paste(small.resize((256 * Z, len(img) * Z)), (0, (y0 + 10) * Z))
        dr.text((2, y0 * Z), '%X' % o, fill=(255, 255, 0))
        y0 += len(img) + 12
    im.save(out)
    print(len(es), 'captions')


if __name__ == '__main__':
    sys.path.insert(0, 'tools')
    d = bytearray(open(ROM, 'rb').read())
    if '--en' in sys.argv:
        d += bytes([0xFF]) * (0x2000000 - len(d))

        class A:
            at = 0x1F80000

            def __call__(self, n):
                o, self.at = self.at, (self.at + n + 3) & ~3
                return o
        apply(d, A())
    show(d, sys.argv[2])
