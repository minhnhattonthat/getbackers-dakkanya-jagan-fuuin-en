"""Item and equipment tables (docs/re/menus.md).
  item table   0xAE7DC, 346 records x 16 bytes: [name list][layout][text][icon]
  equip table  0xAFD7C,  60 records x 20 bytes: [short name list][layout][text][?][?]
name list = u16 indices into the screen charset (FFFF end), drawn with the glyph cache (sysmenu cache screens), so
the build writes English glyph codes there. text = raw glyph codes (full name and/or description) loaded as a
36-glyph dynamic charset; layout = indices 0..n-1 into it, FFFE = line break, FFFF = end.
  python -X utf8 tools/items.py extract    -> script/items.json (keeps existing en)"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT, load_rom, load_glyphs, codes_of  # noqa: E402

PATH = os.path.join(ROOT, 'script', 'items.json')
TABLES = [  # name, start, count, stride, charset literal (to decode the name lists)
    ('item', 0xAE7DC, 346, 16, 0xD938),
    ('equip', 0xAFD7C, 60, 20, 0xC658),
]
TEXT_CELLS = 36       # the dynamic charset loads 36 glyphs (r1 = 0x48 bytes)


def u16list(rom, p):
    out = []
    while len(out) < 80:
        v = struct.unpack_from('<H', rom, p + 2 * len(out))[0]
        if v == 0xFFFF:
            return out
        out.append(v)
    return out


def records():
    for name, start, count, stride, cs in TABLES:
        for i in range(count):
            yield name, i, start + stride * i, cs


def extract():
    rom = load_rom()
    t = load_glyphs()
    t[0x5C3] = '　'
    old = {}
    if os.path.exists(PATH):
        old = {e['id']: e for e in json.load(open(PATH, encoding='utf-8'))}
    out = []
    for name, i, rec, cs in records():
        a, b, c = struct.unpack_from('<3I', rom, rec)
        csp = struct.unpack_from('<I', rom, cs)[0] - 0x08000000
        charset = codes_of(rom[csp:csp + 1024])
        name_jp = ''.join(t.get(charset[k], '?') for k in u16list(rom, a - 0x08000000))
        lay = u16list(rom, b - 0x08000000)
        text = codes_of(rom[c - 0x08000000:c - 0x08000000 + 2 * (max([k for k in lay if k < 0xFFFE] or [0]) + 1)])
        text_jp = ''.join('\n' if k == 0xFFFE else t.get(text[k], '?') for k in lay)
        e = {'id': '%s%03d' % (name, i), 'name_jp': name_jp, 'name_en': '', 'text_jp': text_jp, 'text_en': ''}
        if e['id'] in old:
            e['name_en'] = old[e['id']].get('name_en', '')
            e['text_en'] = old[e['id']].get('text_en', '')
        out.append(e)
    with open(PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('items.json: %d records' % len(out))


def load():
    return json.load(open(PATH, encoding='utf-8')) if os.path.exists(PATH) else []


def lines():
    out = []
    for e in load():
        if e.get('name_en'):
            out.append(e['name_en'])
        if e.get('text_en'):
            out += e['text_en'].split('\n')
    return out


def apply(rom, encoder, alloc):
    """Write English names/texts; returns count. Text = all lines' cells back to back, layout = 0..n with FFFE."""
    byid = {e['id']: e for e in load()}
    n = 0
    for name, i, rec, cs in records():
        e = byid.get('%s%03d' % (name, i))
        if not e:
            continue
        if e.get('name_en'):
            codes = encoder.encode(e['name_en'])
            off = alloc(2 * len(codes) + 2)
            struct.pack_into('<%dH' % (len(codes) + 1), rom, off, *(codes + [0xFFFF]))
            struct.pack_into('<I', rom, rec, 0x08000000 + off)
            n += 1
        if e.get('text_en'):
            cells, lay = [], []
            for k, line in enumerate(e['text_en'].split('\n')):
                if k:
                    lay.append(0xFFFE)
                cs_ = encoder.encode(line)
                lay += list(range(len(cells), len(cells) + len(cs_)))
                cells += cs_
            if len(cells) > TEXT_CELLS:
                raise SystemExit('%s: text needs %d cells > %d' % (e['id'], len(cells), TEXT_CELLS))
            off = alloc(2 * len(cells))
            struct.pack_into('<%dH' % len(cells), rom, off, *cells)
            struct.pack_into('<I', rom, rec + 8, 0x08000000 + off)
            off = alloc(2 * len(lay) + 2)
            struct.pack_into('<%dH' % (len(lay) + 1), rom, off, *(lay + [0xFFFF]))
            struct.pack_into('<I', rom, rec + 4, 0x08000000 + off)
    return n


def allowed():
    """ROM ranges the build may change (pointer words in the tables)."""
    out = []
    for name, i, rec, cs in records():
        out.append((rec, rec + 12))
    return out


if __name__ == '__main__':
    if sys.argv[1:] == ['extract']:
        extract()
    else:
        print(__doc__)
