"""Translation batches for the string bank (script/bank.json).
  python -X utf8 tools/bankbatch.py split          -> work/tl/kNN.tsv (+ terms_kNN.txt)
  python -X utf8 tools/bankbatch.py check <batch>  -> validates work/tl/<batch>.out.tsv
  python -X utf8 tools/bankbatch.py merge <batch>
  python -X utf8 tools/bankbatch.py fix <file.tsv>
Limits: a field gets the screen width the Japanese used (2 halves per JP cell incl. padding), at least `min`,
at most 36 (one box line). Right-aligned fields are re-aligned by the build."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT  # noqa: E402
import enc  # noqa: E402
import batches  # noqa: E402

TL = batches.TL
PATH = os.path.join(ROOT, 'script', 'bank.json')
SPACE = '　'
# (first id, last id, context for the translator, minimum halves)
RANGES = [
    (0, 4, 'battle: skill target label (fixed field)', 10),
    (5, 49, 'battle message FRAGMENT appended right after a name or number: "Ban" + "は毒をうけた！" -> " was poisoned!"; '
            'write a leading underscore _ where a space must follow the name (" was poisoned!" -> _was poisoned!); '
            '0039-0049 element labels', 6),
    (50, 89, 'sound test / gallery menu: help line or track title', 34),
    (90, 101, 'battle: misc line / speaker tag', 12),
    (102, 171, 'battle skill name (menu list)', 16),
    (172, 220, 'skill description, one line, right-aligned by the build', 34),
    (221, 240, 'battle item name (menu list)', 14),
    (241, 300, 'equipment SHORT name in a 4-cell slot: owner + item in 8 characters, e.g. "BanShade"; '
               'use the owner\'s first letters + the item (the full names are elsewhere)', 8),
    (301, 319, 'item description, one line, right-aligned by the build', 34),
    (320, 1041, 'battle voice line or speaker tag ("蛮:" -> "Ban:"); one line', 34),
    (1042, 1157, 'staff credits line (role and/or person). Names of real staff: Western order, Hepburn', 34),
    (1158, 1421, 'character / enemy name ("<神>" = category tag God, <男> Man, <女> Woman, <狂> Mad, <鬼> Demon '
                 '- keep the tag in angle brackets, translated: <God> <Man> <Woman> <Mad> <Demon>); ダミー = Dummy', 16),
    (1422, 1431, 'character epithet (Lady Poison, Dr. Jackal, Beast Master...)', 16),
    (1432, 1604, 'enemy database description, one line', 34),
    (1605, 1787, 'name READING in hiragana (database sort key): write the name in English letters, e.g. '
                 'みどうばん -> Ban Mido', 24),
    (1788, 2368, 'voice clip line (sound test): one line', 34),
    (2369, 2382, 'theme song lyric (sound test): one line; English phrases in the Japanese stay', 34),
]
MAX = 36


def ctx_of(n):
    for a, b, c, m in RANGES:
        if a <= n <= b:
            return c, m
    return 'misc', 12


def cells(s):
    return len(s)


def limit(e):
    n = int(e['id'][1:])
    c, m = ctx_of(n)
    jp = e['jp'].replace('■', '')
    return max(m, min(MAX, 2 * len(jp.rstrip(SPACE)))), c


def skip(e):
    return not e['jp'].replace('■', '').strip(SPACE + ' ')


def load():
    return json.load(open(PATH, encoding='utf-8'))


def plan():
    ents = [e for e in load() if not skip(e)]
    seen, dups, out, cur = {}, {}, [], []
    for e in ents:
        key = e['jp'].strip(SPACE + '■')
        if key in seen:
            dups[e['id']] = seen[key]
            continue
        seen[key] = e['id']
        if len(cur) >= 150:
            out.append(cur)
            cur = []
        cur.append(e)
    if cur:
        out.append(cur)
    return out, dups


def split():
    bs, dups = plan()
    gl = batches.glossary()
    for i, b in enumerate(bs):
        name = 'k%02d' % (i + 1)
        rows, text = [], ''
        for e in b:
            lim, c = limit(e)
            jp = e['jp'].replace('■', '').strip(SPACE)
            rows.append('%s\t%s\tbank\tmax %dch\t%s' % (e['id'], c, lim, jp))
            text += jp
        open(os.path.join(TL, name + '.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
        terms = [r for r in gl if any(j in text for j in r[0])]
        open(os.path.join(TL, 'terms_%s.txt' % name), 'w', encoding='utf-8', newline='\n').write(
            ''.join('%s = %s\n' % (' / '.join(r[0]), ' / '.join(r[1])) for r in terms))
    json.dump({'k%02d' % (i + 1): [e['id'] for e in b] for i, b in enumerate(bs)},
              open(os.path.join(TL, 'bankplan.json'), 'w', encoding='utf-8', newline='\n'), indent=0)
    json.dump(dups, open(os.path.join(TL, 'bankdups.json'), 'w', encoding='utf-8', newline='\n'), indent=0)
    print('bank: %d batches, %d unique, %d repeats' % (len(bs), sum(map(len, bs)), len(dups)))


def check_one(e, en):
    errs = []
    if not en:
        return ['empty']
    if batches.JP_RE.search(en):
        errs.append('Japanese/fullwidth left')
    bad = enc.check_text(en)
    if bad:
        errs.append('characters the font lacks: %r' % ''.join(bad))
    if '\n' in en or '\t' in en:
        errs.append('no line breaks/tabs')
    lim, _ = limit(e)
    if not errs and enc.line_halves(en.strip()) > lim:
        errs.append('too long: %d > %d' % (enc.line_halves(en.strip()), lim))
    return errs


def check(batch):
    ids = json.load(open(os.path.join(TL, 'bankplan.json'), encoding='utf-8'))[batch]
    byid = {e['id']: e for e in load()}
    out = batches.read_out(batch)
    if out is None:
        print('no output file')
        return False
    bad = 0
    for i in ids:
        if i not in out:
            print('  missing', i)
            bad += 1
            continue
        for x in check_one(byid[i], out[i]):
            print('  %s: %s' % (i, x))
            bad += 1
    for i in out:
        if i not in ids and i != '__bad__':
            print('  unknown id', i)
            bad += 1
    print('%s: %s' % (batch, 'OK' if not bad else '%d error(s)' % bad))
    return not bad


def write(updates, status):
    dups = json.load(open(os.path.join(TL, 'bankdups.json'), encoding='utf-8'))
    full = dict(updates)
    for d, f in dups.items():
        if f in updates:
            full[d] = updates[f]
    data = load()
    for e in data:
        if e['id'] in full:
            e['en'] = full[e['id']].strip()
            e['status'] = status
    with open(PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    return len(full)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == 'split':
        split()
        return 0
    if a[0] == 'check':
        return 0 if check(a[1]) else 1
    if a[0] == 'merge':
        if not check(a[1]):
            return 1
        out = batches.read_out(a[1])
        out.pop('__bad__', None)
        print('merged', write(out, 'tl'))
        return 0
    if a[0] == 'fix':
        fixes = {}
        for line in open(a[1], encoding='utf-8-sig').read().splitlines():
            if line.strip():
                i, en = line.split('\t', 1)
                fixes[i.strip()] = en.strip()
        byid = {e['id']: e for e in load()}
        ok = {i: en for i, en in fixes.items() if i in byid and not check_one(byid[i], en)}
        for i in set(fixes) - set(ok):
            print('  rejected', i, check_one(byid[i], fixes[i]) if i in byid else 'unknown')
        print('fixed', write(ok, 'reviewed'))
        return 0
    return 2


if __name__ == '__main__':
    sys.exit(main())
