"""Decode the labels of a charset menu (RE helper for script/sys.json).
usage: python -X utf8 tools/menuscan.py CHARSET_LIT_HEX SLOT_HEX[,SLOT..] [--table START:END:STRIDE[:OFF]]..
  SLOT = ROM address of a word pointing at an index list; a table gives many slots.
Prints a JSON label list (jp decoded through the charset) to paste into script/sys.json."""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import load_rom, load_glyphs, codes_of  # noqa: E402


def main():
    rom = load_rom()
    t = load_glyphs()
    t[0x5C3] = '　'
    cs_ptr = struct.unpack_from('<I', rom, int(sys.argv[1], 16))[0] - 0x08000000
    cs = codes_of(rom[cs_ptr:cs_ptr + 1024])
    slots = []
    for a in sys.argv[2:]:
        if a.startswith('--table'):
            continue
        if ':' in a:
            p = [int(x, 16) for x in a.split(':')]
            start, end, stride = p[:3]
            off = p[3] if len(p) > 3 else 0
            slots += list(range(start + off, end, stride))
        else:
            slots += [int(x, 16) for x in a.split(',')]
    out = []
    for s in slots:
        p = struct.unpack_from('<I', rom, s)[0] - 0x08000000
        idx = []
        while len(idx) < 60:
            v = struct.unpack_from('<H', rom, p + 2 * len(idx))[0]
            if v == 0xFFFF:
                break
            idx.append(v)
        jp = ''.join('\n' if i == 0xFFFE else (t.get(cs[i], '?') if i < len(cs) else '?') for i in idx)
        out.append({'jp': jp, 'en': '', 'lit': '%X' % s})
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
