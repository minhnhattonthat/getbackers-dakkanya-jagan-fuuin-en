"""Find and decompress GBA BIOS LZ77 (type 0x10) blocks: python -X utf8 tools/lzscan.py ROM OUTDIR [min_size]
Writes OUTDIR/<offset hex>.bin for every header (4-aligned) that decompresses cleanly to >= min_size bytes."""
import os
import struct
import sys


def lz77(d, o):
    hdr = struct.unpack_from('<I', d, o)[0]
    if hdr & 0xFF != 0x10:
        return None
    size = hdr >> 8
    if size < 32 or size > 0x40000:
        return None
    out = bytearray()
    p = o + 4
    while len(out) < size:
        if p >= len(d):
            return None
        flags = d[p]
        p += 1
        for b in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> b):
                if p + 1 >= len(d):
                    return None
                x = (d[p] << 8) | d[p + 1]
                p += 2
                n, disp = (x >> 12) + 3, (x & 0xFFF) + 1
                if disp > len(out):
                    return None
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(d[p])
                p += 1
    return bytes(out[:size]), p - o


def main():
    d = open(sys.argv[1], 'rb').read()
    od = sys.argv[2]
    mn = int(sys.argv[3]) if len(sys.argv) > 3 else 256
    os.makedirs(od, exist_ok=True)
    n = 0
    for o in range(0, len(d) - 4, 4):
        if d[o] != 0x10:
            continue
        r = lz77(d, o)
        if r and len(r[0]) >= mn:
            open(os.path.join(od, '%07X.bin' % o), 'wb').write(r[0])
            n += 1
    print('blocks', n)


if __name__ == '__main__':
    main()
