"""Battle UI sprite resources (table around 0xA60600, 7 words each: palette, palette size, tiles, tiles size,
frames table, anim table, flag; e.g. 0xA6062C = command labels). A frame = pieces of 5 words (tile index, x, w | h << 16, 0x01000100, 0xFF) ended by 0xFFFF.
Tiles are 4bpp, 1D: a w x h piece uses (w/8)*(h/8) consecutive tiles, row-major.
    python -X utf8 tools/sprres.py show ENTRY_OFF OUT.png       render every frame of one resource (zoom 2)"""
import struct
import sys

ROM = 'rom/GetBackers Dakkanya - Jagan Fuuin! (Japan).gba'


def resource(d, off):
    """off = table entry (palette, palette size, tiles, tiles size, frames table, anim table, flag)."""
    pal, psz, tiles, tsz, ft = struct.unpack_from('<5I', d, off)
    frames, o = [], ft & 0x1FFFFFF
    while 0x08000000 <= struct.unpack_from('<I', d, o)[0] < 0x0A000000:
        frames.append(struct.unpack_from('<I', d, o)[0] & 0x1FFFFFF)
        o += 4
    return frames, tiles & 0x1FFFFFF


def pieces(d, fo):
    out = []
    while struct.unpack_from('<H', d, fo)[0] != 0xFFFF and len(out) < 32:
        t, x, w, h = struct.unpack_from('<IIHH', d, fo)
        out.append((t, x, w, h))
        fo += 20
    return out


def frame_pixels(d, tiles, fo):
    ps = pieces(d, fo)
    W = max(x + w for t, x, w, h in ps)
    H = max(h for t, x, w, h in ps)
    px = [[0] * W for _ in range(H)]
    for t, x, w, h in ps:
        for ty in range(h // 8):
            for tx in range(w // 8):
                to = tiles + (t + ty * (w // 8) + tx) * 32
                for r in range(8):
                    for c in range(8):
                        b = d[to + r * 4 + c // 2]
                        px[ty * 8 + r][x + tx * 8 + c] = (b >> 4) if c & 1 else (b & 15)
    return px


def write_frame(d, tiles, fo, px):
    for t, x, w, h in pieces(d, fo):
        for ty in range(h // 8):
            for tx in range(w // 8):
                to = tiles + (t + ty * (w // 8) + tx) * 32
                for r in range(8):
                    for c in range(0, 8, 2):
                        y0, x0 = ty * 8 + r, x + tx * 8 + c
                        d[to + r * 4 + c // 2] = px[y0][x0] | (px[y0][x0 + 1] << 4)


def show(d, off, out, cols=4, Z=2):
    from labels import png
    frames, tiles = resource(d, off)
    imgs = [frame_pixels(d, tiles, f) for f in frames]
    W = max(len(i[0]) for i in imgs) + 2
    H = max(len(i) for i in imgs) + 2
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
    print(len(frames), 'frames')


if __name__ == '__main__':
    sys.path.insert(0, 'tools')
    if sys.argv[1] == 'show':
        show(bytearray(open(ROM, 'rb').read()), int(sys.argv[2], 16), sys.argv[3])
