"""Battle menu labels (commands, party names, items, skills): OBJ sprite frames of the battle UI resources
(tools/sprres.py), English names in tools/battle_labels.json (resource entry -> one name per frame).

Each label is a grey panel with the name in ink 3. The job erases the ink, draws the English name in the
proportional font_en, and when the name needs more room it widens the panel (left part + repeated interior column +
right end) and writes the new tiles and a new frame definition to free space. Tile indices are relative to the
resource's tile base (16-bit), so each sheet is first copied to the label area and the new tiles follow it.
Skill costs / item counts: see NUMBERED below. A label slot
in VRAM holds 32 tiles (128 x 16), so a label may be at most 128 px wide.
    python -X utf8 tools/labels.py sheet OUT.png [--en]     render every label (zoom 2), --en = after the redraw
"""
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprres  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = os.path.join(ROOT, 'tools', 'battle_labels.json')
INK, PANEL = 3, 6
LEFT = 6                    # text starts 6 px in (after the slanted left end)
MAXW = 128


def draw_vwf(px, x, y, text, ink, space=3):
    """Proportional font_en text (advance = glyph width + 1, space `space` px); returns the end x."""
    import enc
    for ch in text:
        if ch == ' ':
            x += space
            continue
        g = enc.FONT[ch]
        for r, row in enumerate(g['rows']):
            for c, v in enumerate(row):
                if v == '#':
                    px[y + g['top'] - 1 + r][x + c] = ink
        x += max(len(row) for row in g['rows']) + 1
    return x


def text_width(text, space=3):
    scratch = [[0] * 512 for _ in range(16)]
    return draw_vwf(scratch, 0, 5, text, INK, space) - 1


def encode_piece(px, x0, w):
    b = bytearray()
    for ty in range(2):
        for tx in range(w // 8):
            for r in range(8):
                for c in range(0, 8, 2):
                    y, x = ty * 8 + r, x0 + tx * 8 + c
                    b.append(px[y][x] | (px[y][x + 1] << 4))
    return bytes(b)


def label_jobs(rom):
    names = json.load(open(NAMES, encoding='utf-8'))
    for entry, texts in names.items():
        off = int(entry, 16)
        frames, tiles = sprres.resource(rom, off)
        assert len(frames) == len(texts), (entry, len(frames), len(texts))
        ft = struct.unpack_from('<I', rom, off + 16)[0] & 0x1FFFFFF
        for i, (fo, text) in enumerate(zip(frames, texts)):
            yield off, tiles, ft + 4 * i, fo, text


def relocate(rom, alloc):
    """Copy each resource's tile sheet to `alloc` space and point the resource at the copy: piece tile numbers
    are 16-bit (the game masks them), so new tiles must lie within 2 MiB after the sheet base."""
    for entry in json.load(open(NAMES, encoding='utf-8')):
        off = int(entry, 16)
        tiles, tsz = struct.unpack_from('<II', rom, off + 8)
        tiles &= 0x1FFFFFF
        at = alloc(tsz + 32)
        at = (at + 31) & ~31
        rom[at:at + tsz] = rom[tiles:tiles + tsz]
        struct.pack_into('<I', rom, off + 8, 0x08000000 + at)


# Skill costs and item counts are drawn into fixed tiles of the label's VRAM slot (16x8 px at slot tile k, k+1;
# pieces fill the slot in list order and sit side by side): per character k at 0x3008B8 (skills), k = 20 in the
# literal 0x06010280 of the item list. Skill and item labels become one 128 px layout (4 x 32x16) with the number
# in the right half of the last piece (k = 30, like Ban's original labels).
SKILL_K_TABLE, N_CHARS = 0x3008B8, 10
ITEM_K_LITERALS = (0x5AF54, 0x5B0B8, 0x5B530)
NUMBERED = 128


def numbered(entry, i):
    return entry in ('A60648', 'A60664') or (entry == 'A6062C' and i >= 16)


def widen(px, w):
    """Stretch the panel to w px: left part, the interior column repeated, the last 8 px (right end)."""
    W = len(px[0])
    return [row[:W - 8] + [row[W - 9]] * (w - W) + row[W - 8:] for row in px]


def split_pieces(w):
    out, x = [], 0
    for size in (32, 16, 8):
        while w - x >= size:
            out.append((x, size))
            x += size
    return out


def apply(rom, alloc=None, report=False):
    """Commands and names keep their frame when the English fits (text ends 6 px before the right edge); every
    other label gets fresh tiles in x order and a new frame definition (pieces left to right)."""
    n = 0
    if alloc is not None:
        relocate(rom, alloc)
        for i in range(N_CHARS):
            struct.pack_into('<I', rom, SKILL_K_TABLE + 4 * i, 30)
        for a in ITEM_K_LITERALS:
            assert struct.unpack_from('<I', rom, a)[0] == 0x06010280
            struct.pack_into('<I', rom, a, 0x060103C0)
    names = json.load(open(NAMES, encoding='utf-8'))
    for entry, texts in names.items():
        off = int(entry, 16)
        frames, tiles = sprres.resource(rom, off)
        ft = struct.unpack_from('<I', rom, off + 16)[0] & 0x1FFFFFF
        for i, (fo, text) in enumerate(zip(frames, texts)):
            px = sprres.frame_pixels(rom, tiles, fo)
            px = [[PANEL if v == INK else v for v in row] for row in px]
            W = len(px[0])
            sp = 3
            end = LEFT + text_width(text)          # first column after the text
            if numbered(entry, i):
                w = NUMBERED
                if end + 1 > NUMBERED - 16:        # tighter spaces before the cost column
                    sp = 2
                    end = LEFT + text_width(text, sp)
                assert end + 1 <= NUMBERED - 16, (text, end - LEFT)
            elif end + 6 <= W:
                draw_vwf(px, LEFT, 5, text, INK)
                sprres.write_frame(rom, tiles, fo, px)
                n += 1
                continue
            else:
                w = (end + 6 + 7) & ~7
                assert w <= MAXW, text
            assert alloc is not None, text
            px = widen(px, w)
            draw_vwf(px, LEFT, 5, text, INK, sp)
            pieces = split_pieces(w)
            data = b''.join(encode_piece(px, x, pw) for x, pw in pieces)
            at = alloc(len(data) + 32)
            at += (tiles - at) % 32                 # whole tiles from the sheet base
            rom[at:at + len(data)] = data
            t0 = (at - tiles) // 32
            assert t0 + len(data) // 32 <= 0xFFFF, 'label tiles too far from the sheet base'
            fdef = bytearray()
            for x, pw in pieces:
                fdef += struct.pack('<IIHH', t0, x, pw, 16) + bytes([0, 1, 0, 1, 0xFF, 0, 0, 0])
                t0 += pw // 8 * 2
            fdef += bytes([0xFF, 0xFF, 0, 0])
            fa = alloc(len(fdef))
            rom[fa:fa + len(fdef)] = fdef
            struct.pack_into('<I', rom, ft + 4 * i, 0x08000000 + fa)
            if report and w != W:
                print('widened %-24s %3d -> %3d px' % (text, W, w))
            n += 1
    return n


def png(path, w, h, rows):
    raw = b''.join(b'\0' + bytes(sum(([*p] for p in row), [])) for row in rows)

    def ch(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                           ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))


def sheet(rom, out, Z=2, cols=4):
    imgs = []
    for entry, tiles, slot, fo, text in label_jobs(rom):
        fo = struct.unpack_from('<I', rom, slot)[0] & 0x1FFFFFF
        imgs.append(sprres.frame_pixels(rom, tiles, fo))
    W, H = MAXW + 4, 18
    rows = []
    for k in range(0, len(imgs), cols):
        for y in range(H * Z):
            row = []
            for j in range(cols):
                im = imgs[k + j] if k + j < len(imgs) else [[]]
                for x in range(W * Z):
                    yy, xx = y // Z, x // Z
                    v = im[yy][xx] if yy < len(im) and xx < len(im[yy]) else None
                    row.append((255, 0, 255) if v is None else (v * 17,) * 3)
            rows.append(row)
    png(out, len(rows[0]), len(rows), rows)


if __name__ == '__main__':
    rom = bytearray(open(os.path.join(ROOT, sprres.ROM), 'rb').read())
    if '--en' in sys.argv:
        rom += b'\xff' * (0x2000000 - len(rom))

        class A:
            at = 0x1F00000

            def __call__(self, n):
                o, self.at = self.at, (self.at + n + 3) & ~3
                return o
        apply(rom, A(), report=True)
    sheet(rom, sys.argv[2])
