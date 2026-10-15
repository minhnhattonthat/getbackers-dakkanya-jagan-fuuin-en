"""GBA BIOS LZ77 (type 0x10) compressor, VRAM-safe (no back-reference closer than 2 bytes).
    compress(data) -> bytes; selftest: python -X utf8 tools/lzcomp.py"""
import struct


def compress(data, min_disp=2):
    out = bytearray(struct.pack('<I', 0x10 | (len(data) << 8)))
    i, n = 0, len(data)
    chains = {}                     # 3-byte prefix -> positions (ascending)

    def add(p):
        if p + 3 <= n:
            chains.setdefault(data[p:p + 3], []).append(p)
    added = 0
    while i < n:
        flag_at = len(out)
        out.append(0)
        flags = 0
        for b in range(8):
            if i >= n:
                break
            while added < i - min_disp + 1:
                add(added)
                added += 1
            best_len, best_disp = 0, 0
            maxlen = min(18, n - i)
            if maxlen >= 3:
                for j in reversed(chains.get(data[i:i + 3], ())):
                    if i - j > 0x1000:
                        break
                    k = 3
                    while k < maxlen and data[j + k] == data[i + k]:
                        k += 1
                    if k > best_len:
                        best_len, best_disp = k, i - j
                        if k == maxlen:
                            break
            if best_len >= 3:
                flags |= 0x80 >> b
                x = ((best_len - 3) << 12) | (best_disp - 1)
                out += bytes([x >> 8, x & 0xFF])
                i += best_len
            else:
                out.append(data[i])
                i += 1
        out[flag_at] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lzscan
    for sample in (b'', b'abcabcabcabcxyz' * 40, os.urandom(3000), bytes(5000)):
        if not sample:
            continue
        c = compress(sample)
        assert lzscan.lz77(c, 0)[0] == sample
    print('lzcomp selftest ok')
