"""Act title cards ("Act1 「...」"): table 0x0809BADC, 16 bytes per act 0-9 = [4bpp tiles, 30x20 map, palette,
tile bytes]. Tiles are raw in ROM (DMA to VRAM 0x06004000, BG0).
  python -X utf8 tools/actcards.py show   -> work/act_<n>.png (2x)
apply(rom) redraws each card's text from ACT_TITLES (tiles rewritten in place; extra tiles are not needed because
the text area keeps its own tiles)."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = 0x9BADC
W, H = 30, 20


def card(rom, n):
    tiles, mp, pal, nbytes = struct.unpack_from('<4I', rom, TABLE + 16 * n)
    return tiles - 0x08000000, mp - 0x08000000, pal - 0x08000000, nbytes


def compose(rom, n):
    t0, mp, pal, nb = card(rom, n)
    img = [[0] * (W * 8) for _ in range(H * 8)]
    ents = []
    for cy in range(H):
        for cx in range(W):
            e = struct.unpack_from('<H', rom, mp + 2 * (cy * W + cx))[0]
            t, hf, vf = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1
            ents.append((cx, cy, t, hf, vf))
            o = t0 + t * 32
            for r in range(8):
                for c in range(8):
                    b = rom[o + r * 4 + c // 2]
                    v = (b >> (4 * (c & 1))) & 15
                    img[cy * 8 + (7 - r if vf else r)][cx * 8 + (7 - c if hf else c)] = v
    return img, ents


def palette(rom, n):
    pal = card(rom, n)[2]
    cols = [struct.unpack_from('<H', rom, pal + 2 * i)[0] for i in range(16)]
    return [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in cols]


def show(rom):
    from PIL import Image
    for n in range(10):
        img, _ = compose(rom, n)
        rgb = palette(rom, n)
        im = Image.new('RGB', (W * 8, H * 8))
        im.putdata([rgb[v] for row in img for v in row])
        im.resize((W * 16, H * 16), Image.NEAREST).save(os.path.join(ROOT, 'work', 'act_%d.png' % n))


# act n -> title line, drawn centred in TEXT_RECT (the Japanese title line; "Act.N" above is kept)
ACT_TITLES = {
    0: 'Get Back the Mystery Game!',
    1: '"Get Back the Magic Camera!"',
    2: '"Retrieve the Keepsake!"',
    3: '"Operation: Kannagi Masks!"',
    4: '"Hiruta\'s Request"',
    5: '"Operation: Girl Retrieval!"',
    6: '"Evil Eye Sealed"',
    7: '"The Last Retrieval"',
    8: '"Retrieval, Once Again!"',
    9: 'Operation: True Metropolis!!',
}
TEXT_RECT = (0, 74, 240, 96)
ADV = 8


def apply(rom, alloc):
    """Copy each card's tiles + map to free space, give every cell of TEXT_RECT its own new tile, draw the English
    title there and repoint the table (tile pointer, map pointer, tile byte count)."""
    n_done = 0
    for n, line in ACT_TITLES.items():
        img, ents = compose(rom, n)
        x0, y0, x1, y1 = TEXT_RECT
        bg, ink, outline = ACT_COLOURS
        gfx.fill(img, TEXT_RECT, bg)
        w = gfx.text_width(line, ADV)
        gfx.draw_text(img, (x0 + x1 - w) // 2, y0 + 2, line, ink, outline, ADV, sy=2, bold=True)
        t0, mp, pal, nb = card(rom, n)
        tiles = bytearray(rom[t0:t0 + nb])
        mapw = bytearray(rom[mp:mp + 2 * W * H])
        for (cx, cy, t, hf, vf) in ents:
            if not (x0 // 8 <= cx < (x1 + 7) // 8 and y0 // 8 <= cy < (y1 + 7) // 8):
                continue
            px = [[img[cy * 8 + r][cx * 8 + c] for c in range(8)] for r in range(8)]
            new_t = len(tiles) // 32
            tiles += bytes((row[c] & 15) | ((row[c + 1] & 15) << 4) for row in px for c in range(0, 8, 2))
            e = struct.unpack_from('<H', mapw, 2 * (cy * W + cx))[0]
            struct.pack_into('<H', mapw, 2 * (cy * W + cx), (e & 0xF000) | new_t)
        assert len(tiles) // 32 < 512, 'act %d: too many tiles' % n
        to = alloc(len(tiles))
        rom[to:to + len(tiles)] = tiles
        mo = alloc(len(mapw))
        rom[mo:mo + len(mapw)] = mapw
        struct.pack_into('<3I', rom, TABLE + 16 * n, 0x08000000 + to, 0x08000000 + mo, 0x08000000 + pal)
        struct.pack_into('<I', rom, TABLE + 16 * n + 12, len(tiles))
        n_done += 1
    return n_done


ACT_COLOURS = (0, 5, 13)    # transparent, dark olive ink, white outline (as the original lettering)


def allowed(rom):
    out = []
    for n in range(10):
        t0, mp, pal, nb = card(rom, n)
        out.append((t0, t0 + nb))
    return out


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from textlib import load_rom
    if sys.argv[1:] == ['show']:
        show(load_rom())
