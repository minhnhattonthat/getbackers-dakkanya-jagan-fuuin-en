"""GetBackers Dakkanya - Jagan Fuuin! (GBA) English build.
usage: python -X utf8 build.py identity          rebuild from the JP text, must equal the original ROM
       python -X utf8 build.py marker            every message -> its id + filler (box/width tour)
       python -X utf8 build.py build [ID=text]   English build (overrides go to build/getbackers_qa.gba)
       python -X utf8 build.py release           gate + BPS + zip (tools/release.py)"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from textlib import ROOT, load_rom, load_glyphs, find_scripts, parse_script, is_cmd, codes_of  # noqa: E402
from extract import messages, BANK, SPACE  # noqa: E402
import enc  # noqa: E402
import fontlib  # noqa: E402
import layout  # noqa: E402
import sysmenu  # noqa: E402
import menuasm  # noqa: E402
import items  # noqa: E402
import gfx  # noqa: E402
import actcards  # noqa: E402

OUT = {'identity': 'getbackers_identity.gba', 'marker': 'getbackers_marker.gba', 'build': 'getbackers_en.gba',
       'qa': 'getbackers_qa.gba'}
SCRIPT_START = 0xEE1AC4
BANK_PTR = 0x058174
REF_RANGES = [(0x0, 0xB0000), (0xED0000, SCRIPT_START)]   # where script pointers live (code pools + tables)
FREE_END = 0xFE0000                         # 0xFE0000-0xFE4000 holds code/data, keep
EXT_START, EXT_END = 0x1000000, 0x2000000   # overflow area when the ROM has to grow


def rec(payload):
    return struct.pack('<I', len(payload)) + payload


def txt(codes):
    if len(codes) % 2:
        codes = codes + [enc.SPACE_CODE]
    return rec(struct.pack('<%dH' % len(codes), *codes))


def cmd(op, *args):
    return rec(struct.pack('<%dI' % (1 + len(args)), op, *args))


def load_json(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return json.load(f)


def load_text():
    """id -> entry for every dlg/bank entry; names jp -> en."""
    ents = {}
    d = os.path.join(ROOT, 'script', 'dlg')
    for fn in sorted(os.listdir(d)):
        for e in load_json(os.path.join('script', 'dlg', fn)):
            ents[e['id']] = e
    for e in load_json(os.path.join('script', 'bank.json')):
        ents[e['id']] = e
    names = {e['jp']: e['en'] for e in load_json(os.path.join('script', 'names.json'))}
    return ents, names


def english_for(mode, e, overrides):
    """English text for an entry or None (= keep the original bytes)."""
    if e['id'] in overrides:
        return overrides[e['id']]
    if mode == 'marker':
        return layout.marker(e)
    if mode in ('build', 'qa') and e.get('en') and e.get('status') != 'skip':
        return e['en']
    return None


def plan(rom, t, mode, overrides):
    """Per script: list of (record index range to replace, list of ('lines'|'cmd', ...)) and all English lines."""
    ents, names = load_text()
    jobs = {}
    lines_all = []
    for s in sorted(find_scripts(rom)):
        if s == BANK:
            continue
        subs = []
        choice_w = {}     # 0C command record index -> widest English option (cells)
        for n, u in enumerate(messages(rom, s, t)):
            if u['kind'] in ('name', 'bname'):
                if mode == 'identity':
                    continue
                key = u['jp'].rstrip(SPACE)
                en = layout.name_marker(key) if mode == 'marker' else names.get(key)
                if en:
                    subs.append((u['recs'], [('txt', en)]))
                    lines_all.append(en)
                continue
            e = ents['%06X:%d' % (s, n)]
            en = english_for(mode, e, overrides)
            if en is None:
                continue
            idxs, new = layout.emit(u, en)
            subs.append((idxs, new))
            lines_all += [x[1] for x in new if x[0] == 'txt']
            if u['kind'] == 'choice':
                choice_w[u['cmd']] = max(choice_w.get(u['cmd'], 0), enc.cell_width(en))
        recs = None
        for ci, cells in choice_w.items():
            recs = recs or parse_script(rom, s)[0]
            subs.append(([ci], [('cmd', layout.choice_cmd(recs[ci][1], cells))]))
        if subs:
            jobs[s] = subs
    bank_en = {}
    brecs = parse_script(rom, BANK)[0]
    for i, (q, p) in enumerate(brecs):
        e = ents.get('B%04d' % i)
        if e is None:
            break
        en = english_for(mode, e, overrides)
        if en is not None:
            bank_en[i] = en
            lines_all.append(bank_text(codes_of(p), en))
    return jobs, bank_en, lines_all


def rebuild_script(rom, s, subs, encoder):
    recs, end = parse_script(rom, s)
    by_first = {}
    drop = set()
    for idxs, new in subs:
        by_first[idxs[0]] = new
        drop.update(idxs)
    out = bytearray(b'PAC3')
    for i, (q, p) in enumerate(recs):
        if i in by_first:
            for kind, v in by_first[i]:
                out += txt(encoder.encode(v)) if kind == 'txt' else cmd(*v)
        elif i not in drop:
            out += rec(p)
    return bytes(out)


BLANKS = (enc.SPACE_CODE, 0x6AE)
SYS_START, SYS_END = 0xFE4000, 0xFFF000     # menu charsets / index lists (free 0xFF fill)


class Alloc:
    def __init__(self, lo, hi):
        self.at, self.hi = lo, hi

    def __call__(self, n):
        off = self.at
        self.at = (self.at + n + 3) & ~3
        if self.at > self.hi:
            raise SystemExit('menu data area full')
        return off


def bank_layout(codes):
    """-> (leading full spaces, body cells, trailing blank codes) of a JP bank string."""
    lead = 0
    while lead < len(codes) and codes[lead] == enc.SPACE_CODE:
        lead += 1
    end = len(codes)
    while end > lead and codes[end - 1] in BLANKS:
        end -= 1
    return lead, end - lead, codes[end:]


def bank_text(jp_codes, en):
    """English for a bank string, keeping the JP field layout: right-aligned fields (leading spaces) stay
    right-aligned to where the JP text ended."""
    lead, body, trail = bank_layout(jp_codes)
    if en.startswith('_'):            # translators mark a leading space (fragments after a name) with _
        en = ' ' + en[1:]
    if lead:
        width = 2 * (lead + body)
        en = ' ' * max(0, width - enc.line_halves(en)) + en
    return en


def bank_codes(jp_codes, en, encoder):
    """... plus the trailing blank/filler codes kept as they were."""
    return encoder.encode(bank_text(jp_codes, en)) + list(bank_layout(jp_codes)[2])


def build(mode, overrides=None):
    overrides = overrides or {}
    rom = bytearray(load_rom())
    orig = bytes(rom)
    t = load_glyphs()
    jobs, bank_en, lines_all = plan(orig, t, mode, overrides)
    encoder = None
    if mode != 'identity':
        # 0x6AE = blank filler glyph used by bank strings; 0x7FF holds the menu-cache trampolines
        encoder = enc.Encoder(reserved={0x6AE, 0x7FF})
        if mode in ('build', 'qa'):
            lines_all += sysmenu.lines() + items.lines()
        for ln in lines_all:
            encoder.add(ln)
        encoder.freeze()
        for code, px in encoder.glyphs().items():
            o = fontlib.glyph_off(code)
            rom[o:o + 0x80] = fontlib.encode_glyph(px)
        if mode in ('build', 'qa'):
            if sysmenu.uses_cache():
                menuasm.apply(rom, SYS_START, fontlib.glyph_off(menuasm.TRAMP_CODE))
            alloc = Alloc(SYS_START + 0x400, SYS_END)
            sysmenu.apply(rom, encoder, alloc)
            items.apply(rom, encoder, alloc)
            gfx.apply(rom)
            actcards.apply(rom, alloc)
    # repack scripts contiguously in ROM order (4 zero bytes after each, like the original: some scripts
    # are reached only by walking on from the previous one, so order and spacing must not change)
    scripts = sorted(s for s in find_scripts(orig) if s != BANK)
    blob = bytearray()
    rel = {}
    for s in scripts:
        rel[s] = len(blob)
        if s in jobs:
            blob += rebuild_script(orig, s, jobs[s], encoder)
        else:
            blob += orig[s:parse_script(orig, s)[1]]
        blob += b'\0\0\0\0'
    brecs, bend = parse_script(orig, BANK)
    bank = bytearray(b'PAC3')
    for i, (q, p) in enumerate(brecs):
        bank += txt(bank_codes(codes_of(p), bank_en[i], encoder)) if i in bank_en else rec(p)
    # placement: original area (up to FREE_END) first; overflow goes past 16 MiB (ROM grows to 32 MiB)
    if SCRIPT_START + len(blob) + len(bank) <= FREE_END:
        script_at, bank_at = SCRIPT_START, SCRIPT_START + len(blob)
    elif SCRIPT_START + len(blob) <= FREE_END:
        script_at, bank_at = SCRIPT_START, EXT_START
    else:
        script_at, bank_at = EXT_START, EXT_START + len(blob)
    rom[SCRIPT_START:bend] = b'\xff' * (bend - SCRIPT_START)
    for at, data in ((script_at, blob), (bank_at, bank)):
        if at + len(data) > len(rom):
            rom += b'\xff' * (EXT_END - len(rom))
        if at + len(data) > (FREE_END if at < EXT_START else EXT_END):
            raise SystemExit('text area overflow at %X (+%X)' % (at, len(data)))
        rom[at:at + len(data)] = data
    total_end = max(script_at + len(blob), bank_at + len(bank))
    # repoint
    for lo, hi in REF_RANGES:
        for i in range(lo, hi, 4):
            v = struct.unpack_from('<I', orig, i)[0] - 0x08000000
            if v in rel:
                struct.pack_into('<I', rom, i, 0x08000000 + script_at + rel[v])
    struct.pack_into('<I', rom, BANK_PTR, 0x08000000 + bank_at)
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    name = OUT['qa' if overrides else mode]
    path = os.path.join(ROOT, 'build', name)
    with open(path, 'wb') as f:
        f.write(rom)
    with open(path + '.map.json', 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'scripts': {'%06X' % s: 0x08000000 + script_at + r for s, r in rel.items()},
                   'bank': 0x08000000 + bank_at}, f, indent=0)
    info = {'path': path, 'pairs': len(encoder.pairs) if encoder else 0, 'end': total_end}
    return bytes(rom), info


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('identity', 'marker', 'build', 'release'):
        print(__doc__)
        return 2
    mode = sys.argv[1]
    if mode == 'release':
        import release
        return release.main()
    ov = dict(a.split('=', 1) for a in sys.argv[2:])
    rom, info = build(mode, ov)
    if mode == 'identity':
        same = rom == load_rom()
        print('identity:', 'identical' if same else 'DIFFERENT')
        return 0 if same else 1
    print('%s -> %s (digraphs %d, text area ends %X)' % (mode, info['path'], info['pairs'], info['end']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
