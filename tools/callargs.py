"""Print the register setup before every BL to a function (r0-r3 literal loads / movs immediates), for RE of the
menu text calls. usage: python -X utf8 tools/callargs.py FUNC_HEX [FUNC_HEX ..]"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import load_rom, load_glyphs, codes_of, decode  # noqa: E402

try:
    import capstone
except ImportError:
    raise SystemExit('pip install capstone')


def bl_sites(rom, target):
    out = []
    for i in range(0, 0x100000, 2):
        hi, lo = struct.unpack_from('<HH', rom, i)
        if hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800:
            off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
            if off & 0x400000:
                off -= 0x800000
            if 0x08000000 + i + 4 + off == target:
                out.append(0x08000000 + i)
    return out


def regs_before(rom, md, site, back=24):
    regs = {}
    start = site - back * 2
    code = rom[start - 0x08000000:site - 0x08000000]
    for ins in md.disasm(code, start):
        ops = ins.op_str.replace(' ', '')
        if ins.mnemonic in ('movs', 'mov') and ops[:2] in ('r0', 'r1', 'r2', 'r3') and '#' in ops:
            regs[ops[:2]] = ('imm', int(ops.split('#')[1], 0), ins.address)
        elif ins.mnemonic == 'ldr' and ops[:2] in ('r0', 'r1', 'r2', 'r3') and '[pc' in ops:
            disp = int(ops.split('#')[1].rstrip(']'), 0) if '#' in ops else 0
            lit = ((ins.address + 4) & ~3) + disp
            val = struct.unpack_from('<I', rom, lit - 0x08000000)[0]
            regs[ops[:2]] = ('lit', val, lit)
        elif ins.mnemonic == 'bl':
            regs = {}
    return regs


def main():
    rom = load_rom()
    t = load_glyphs()
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    for f in sys.argv[1:]:
        target = int(f, 16)
        print('== %08X' % target)
        for s in bl_sites(rom, target):
            r = regs_before(rom, md, s)
            desc = []
            for k in ('r0', 'r1', 'r2', 'r3'):
                if k in r:
                    kind, v, at = r[k]
                    desc.append('%s=%s%X@%X' % (k, '' if kind == 'imm' else '*', v, at))
            txt = ''
            if 'r0' in r and r['r0'][0] == 'lit' and 0x08000000 <= r['r0'][1] < 0x09000000:
                p = r['r0'][1] - 0x08000000
                n = r.get('r1', ('', 16, 0))[1] if r.get('r1', ('',))[0] == 'imm' else 32
                txt = decode(codes_of(rom[p:p + min(n, 80)]), t)
            print('%08X %s  %s' % (s, ' '.join(desc), txt))


if __name__ == '__main__':
    main()
