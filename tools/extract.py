"""Dump every translatable string from the ORIGINAL ROM into script/*.json. Never clobbers English:
existing files keep their en/status/notes; jp/kind/speaker fields are refreshed.
usage: python -X utf8 tools/extract.py

Outputs
  script/dlg/dNN.json  PAC3 script messages, 40 scripts per file, in ROM order
  script/bank.json     string bank at 0xFB6034 (battle messages, skill names, sound test...), id B0000..
  script/names.json    speaker names (name tags after cmd 80000008 / 9F000004 / A0000002), jp -> en
Entry fields: id, kind, speaker, jp, en, status, notes (+ max for fixed-width kinds)."""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT, load_rom, load_glyphs, find_scripts, parse_script, is_cmd, codes_of, decode

BANK = 0xFB6034
PER_FILE = 40
SPACE = '　'


def op_of(p):
    return struct.unpack_from('<I', p)[0]


def is_end(p):
    return p[:4] == b'\xff\xff\xff\xff'


def messages(rom, off, t):
    """Yield message units of one script: dicts with kind, speaker, jp (lines joined by \\n), recs (indices)."""
    recs, _ = parse_script(rom, off)
    speaker = ''
    i = 0
    n = 0
    while i < len(recs):
        q, p = recs[i]
        if not is_cmd(p):
            i += 1
            continue
        op = op_of(p)
        texts = []
        j = i + 1
        while j < len(recs) and not is_cmd(recs[j][1]) and not is_end(recs[j][1]):
            texts.append(j)
            j += 1
        if not texts:
            i = j
            continue
        dec = [decode(codes_of(recs[k][1]), t) for k in texts]
        if op == 0x80000008:
            for k, d in zip(texts, dec):
                yield dict(kind='name', jp=d, recs=[k], op=op)
            speaker = dec[0].rstrip(SPACE)
        elif op in (0x9F000004, 0xA0000002):
            # battle cut-in: name line ("松風:") then one message line
            speaker = dec[0].rstrip(SPACE).rstrip(':')
            yield dict(kind='bname', jp=dec[0], recs=[texts[0]], op=op)
            for k, d in zip(texts[1:], dec[1:]):
                yield dict(kind='bline', speaker=speaker, jp=d, recs=[k], op=op)
        elif op in (0x8000000A, 0x8000000B):
            yield dict(kind='msg', speaker=speaker, jp='\n'.join(d.rstrip(SPACE) for d in dec), recs=texts, op=op)
        elif op == 0x8000000C:
            for k, d in zip(texts, dec):
                yield dict(kind='choice', speaker=speaker, jp=d.rstrip(SPACE), recs=[k], op=op, cmd=i)
        elif op == 0xA0000001:
            yield dict(kind='prompt', speaker=speaker, jp='\n'.join(d.rstrip(SPACE) for d in dec), recs=texts, op=op)
        else:
            raise SystemExit('text after unknown op %08X at %X' % (op, q))
        i = j


def script_units(rom, t):
    """[(script_off, [unit...])] for every script except the bank."""
    out = []
    for s in sorted(find_scripts(rom)):
        if s == BANK:
            continue
        out.append((s, list(messages(rom, s, t))))
    return out


def merge(path, entries):
    """Write entries, keeping en/status/notes from an existing file (keyed by id)."""
    old = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            old = {e['id']: e for e in json.load(f)}
    for e in entries:
        o = old.get(e['id'])
        if o:
            for k in ('en', 'status', 'notes'):
                if k in o:
                    e[k] = o[k]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
        f.write('\n')


def main():
    rom = load_rom()
    t = load_glyphs()
    t[0x5C3] = SPACE
    units = script_units(rom, t)
    names = {}
    files = {}
    for si, (s, us) in enumerate(units):
        fn = 'd%02d' % (si // PER_FILE)
        for n, u in enumerate(us):
            if u['kind'] in ('name', 'bname'):
                key = u['jp'].rstrip(SPACE)
                names.setdefault(key, {'jp': key, 'en': '', 'count': 0})
                names[key]['count'] += 1
                continue
            e = {'id': '%06X:%d' % (s, n), 'kind': u['kind'], 'speaker': u.get('speaker', ''), 'jp': u['jp'],
                 'en': '', 'status': ''}
            files.setdefault(fn, []).append(e)
    for fn, es in files.items():
        merge(os.path.join(ROOT, 'script', 'dlg', fn + '.json'), es)
    # names: keep existing en
    npath = os.path.join(ROOT, 'script', 'names.json')
    old = {}
    if os.path.exists(npath):
        with open(npath, encoding='utf-8') as f:
            old = {e['jp']: e for e in json.load(f)}
    nl = sorted(names.values(), key=lambda e: -e['count'])
    for e in nl:
        if e['jp'] in old:
            e['en'] = old[e['jp']]['en']
    with open(npath, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(nl, f, ensure_ascii=False, indent=1)
        f.write('\n')
    # bank
    recs, _ = parse_script(rom, BANK)
    bank = [{'id': 'B%04d' % i, 'kind': 'bank', 'jp': decode(codes_of(p), t), 'en': '', 'status': ''}
            for i, (q, p) in enumerate(recs)]
    merge(os.path.join(ROOT, 'script', 'bank.json'), bank)
    print('scripts %d, dlg entries %d in %d files, names %d, bank %d' % (
        len(units), sum(len(v) for v in files.values()), len(files), len(nl), len(bank)))


if __name__ == '__main__':
    main()
