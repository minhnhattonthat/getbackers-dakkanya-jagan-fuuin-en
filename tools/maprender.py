"""Field map data (table at 0x1B34C8, 7 words: size (u16 w, u16 h in tiles? ), palette LZ, tiles LZ, layer maps
LZ x3, 0). Renders a map's layers for the sign survey: python -X utf8 tools/maprender.py ENTRY W OUT.png"""
import struct
import sys
sys.path.insert(0, 'tools')
import lzscan  # noqa: E402

ROM = 'rom/GetBackers Dakkanya - Jagan Fuuin! (Japan).gba'


def lz(d, p):
    return lzscan.lz77(d, p & 0x1FFFFFF)[0]


def render(d, entry, W, layers=(2, 1, 0)):
    from PIL import Image
    dims, pp, tp, m1, m2, m3, z = struct.unpack_from('<7I', d, entry)
    pal, til = lz(d, pp), lz(d, tp)
    cols = [struct.unpack_from('<H', pal, 2 * i)[0] for i in range(len(pal) // 2)]
    rgb = [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in cols]
    maps = [lz(d, m) for m in (m1, m2, m3)]
    H = len(maps[0]) // 2 // (W * 2) * 2      # whole rows of 16x16 blocks
    im = Image.new('RGB', (W * 8, H * 8))
    px = im.load()
    for li in layers:
        mp = maps[li]
        for cy in range(min(H, len(mp) // 2 // (W * 2) * 2)):
            for cx in range(W):
                # 16x16 blocks of 2x2 tiles, blocks row-major (W in tiles)
                k = ((cy // 2) * (W // 2) + cx // 2) * 4 + (cy & 1) * 2 + (cx & 1)
                e = struct.unpack_from('<H', mp, 2 * k)[0]
                n, hf, vf, pl = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, e >> 12
                for r in range(8):
                    for c in range(8):
                        rr, cc = (7 - r if vf else r), (7 - c if hf else c)
                        o = n * 32 + rr * 4 + cc // 2
                        if o >= len(til):
                            continue
                        b = til[o]
                        v = (b >> 4) if cc & 1 else b & 15
                        if v and pl * 16 + v < len(rgb):
                            px[cx * 8 + c, cy * 8 + r] = rgb[pl * 16 + v]
    return im


if __name__ == '__main__':
    d = open(ROM, 'rb').read()
    render(d, int(sys.argv[1], 16), int(sys.argv[2])).save(sys.argv[3])
