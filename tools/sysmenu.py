"""Menu text drawn from glyph "charsets" (docs/re/menus.md).

A charset is a list of glyph codes rendered once into VRAM (0x0800FA2C: r0 = list, r1 = BYTE count, r2 = first
tile); a label is a list of u16 indices into the charset drawn by 0x0800FAAC (r0 = list, r1 = BYTE count, x, y).
script/sys.json describes, per screen, the literal-pool word holding each pointer and the address of the
`movs rN, #imm8` that holds each byte count. The build writes a new charset (the English cells of all labels of
the screen, deduplicated) and new index lists into free space, repoints the literals and patches the immediates.
A charset must not grow beyond its original glyph count (VRAM budget)."""
import json
import os
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'script', 'sys.json')


def load():
    if not os.path.exists(PATH):
        return []
    with open(PATH, encoding='utf-8') as f:
        return json.load(f)


def lines():
    """English strings to feed the digraph encoder."""
    out = []
    for scr in load():
        for lab in scr['labels']:
            if lab.get('en'):
                out += lab['en'].split('\n')
    return out


def patch_imm(rom, addr, value):
    """addr = THUMB `movs rN, #imm8` (high byte 0x20-0x27)."""
    assert 0x20 <= rom[addr + 1] <= 0x27, 'not a movs imm8 at %X' % addr
    assert 0 <= value <= 255, 'immediate %d too big at %X' % (value, addr)
    rom[addr] = value


def uses_cache():
    return any(s.get('cache') for s in load())


def apply_cache(rom, encoder, alloc, scr):
    """Cache-mode screen (tools/menuasm.py): charset literal -> descriptor FFFD,k,first k original codes (glyphs
    the game draws by index, e.g. digits); labels -> glyph-code lists (FFFF-terminated)."""
    lit = int(scr['charset_lit'], 16)
    old = struct.unpack_from('<I', rom, lit)[0] - 0x08000000
    k = scr.get('keep', 0)
    pre = list(struct.unpack_from('<%dH' % k, rom, old)) if k else []
    d = alloc(4 + 2 * k)
    struct.pack_into('<%dH' % (2 + k), rom, d, 0xFFFD, k, *pre)
    struct.pack_into('<I', rom, lit, 0x08000000 + d)
    for l in scr['labels']:
        if not l.get('lit') or not l.get('en'):
            continue
        codes = []
        for i, line in enumerate(l['en'].split('\n')):     # FFFE = line break (draw_label_ff)
            codes += ([0xFFFE] if i else []) + encoder.encode(line)
        off = alloc(2 * len(codes) + 2)
        struct.pack_into('<%dH' % (len(codes) + 1), rom, off, *(codes + [0xFFFF]))
        for a in str(l['lit']).split(','):
            struct.pack_into('<I', rom, int(a, 16), 0x08000000 + off)
        if l.get('imm'):
            patch_imm(rom, int(l['imm'], 16), 2 * len(codes))


def apply(rom, encoder, alloc):
    """Write every screen whose labels all have English. alloc(nbytes) -> ROM offset (4-aligned)."""
    done = 0
    for scr in load():
        labs = scr['labels']
        if scr.get('cache'):
            if any(l.get('en') for l in labs):
                apply_cache(rom, encoder, alloc, scr)
                done += 1
            continue
        if not labs or not all(l.get('en') for l in labs):
            continue
        cells = []
        idx_lists = []
        for l in labs:
            codes = encoder.encode(l['en'])
            idx = []
            for c in codes:
                if c not in cells:
                    cells.append(c)
                idx.append(cells.index(c))
            idx_lists.append(idx)
        if len(cells) > scr['glyphs']:
            raise SystemExit('menu %s: %d cells > %d glyph budget' % (scr['id'], len(cells), scr['glyphs']))
        cs_off = alloc(2 * len(cells))
        struct.pack_into('<%dH' % len(cells), rom, cs_off, *cells)
        struct.pack_into('<I', rom, int(scr['charset_lit'], 16), 0x08000000 + cs_off)
        patch_imm(rom, int(scr['charset_imm'], 16), 2 * len(cells))
        for l, idx in zip(labs, idx_lists):
            if not l.get('lit'):
                continue
            off = alloc(2 * len(idx) + 2)
            struct.pack_into('<%dH' % (len(idx) + 1), rom, off, *(idx + [0xFFFF]))
            struct.pack_into('<I', rom, int(l['lit'], 16), 0x08000000 + off)
            if l.get('imm'):
                patch_imm(rom, int(l['imm'], 16), 2 * len(idx))
        done += 1
    return done
