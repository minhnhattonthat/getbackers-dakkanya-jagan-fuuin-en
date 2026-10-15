"""Translation batches for the dialogue (script/dlg/*.json).
  python -X utf8 tools/batches.py split            -> work/tl/bNNN.tsv + work/tl/terms_bNNN.txt, work/tl/dups.json
  python -X utf8 tools/batches.py check <batch>    -> validates work/tl/<batch>.out.tsv; prints OK or the bad ids
  python -X utf8 tools/batches.py merge <batch>    -> check, then write the English into script/dlg/*.json
                                                      (also fills later repeats of the same speaker+line)
  python -X utf8 tools/batches.py fix <file.tsv>   -> apply id<TAB>English fixes (checked) to any entries
  python -X utf8 tools/batches.py list             -> batches with entry counts and merge status
Batches follow story (ROM) order; a line already given to an earlier batch (same speaker + same Japanese) is not
repeated, the merge copies its English."""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT  # noqa: E402
import enc  # noqa: E402
import layout  # noqa: E402

TL = os.path.join(ROOT, 'work', 'tl')
MAX_CHARS, MAX_ROWS = 3300, 140
JP_RE = re.compile(r'[぀-ヿ一-鿿＀-￯]')
SPACE = '　'


def load_dlg():
    files = sorted(glob.glob(os.path.join(ROOT, 'script', 'dlg', '*.json')))
    return [(f, json.load(open(f, encoding='utf-8'))) for f in files]


def names():
    return {e['jp']: e['en'] for e in json.load(open(os.path.join(ROOT, 'script', 'names.json'), encoding='utf-8'))}


def skip(e):
    return not e['jp'].strip(SPACE + ' \n')


def limit_text(kind):
    w, n = layout.LIMITS[kind]
    if kind == 'msg':
        return 'box %dch x %d lines (longer = extra box)' % (w, n)
    return 'max %dch, 1 line' % w


def plan():
    """-> list of batches (list of entries), dups {id: first_id}."""
    seen = {}
    dups = {}
    out, cur, chars = [], [], 0
    for f, ents in load_dlg():
        for e in ents:
            if skip(e) or e.get('status') == 'reviewed':   # pilot / hand-fixed lines stay out of batches
                continue
            key = (e['speaker'], e['jp'], e['kind'])
            if key in seen:
                dups[e['id']] = seen[key]
                continue
            seen[key] = e['id']
            if cur and (chars + len(e['jp']) > MAX_CHARS or len(cur) >= MAX_ROWS):
                out.append(cur)
                cur, chars = [], 0
            cur.append(e)
            chars += len(e['jp'])
    if cur:
        out.append(cur)
    return out, dups


def bname(i):
    return 'b%03d' % (i + 1)


def glossary():
    rows = []
    for line in open(os.path.join(ROOT, 'glossary.md'), encoding='utf-8'):
        if line.startswith('| ') and not line.startswith('| JP') and not line.startswith('|---'):
            c = [x.strip() for x in line.strip().strip('|').split('|')]
            if len(c) >= 2:
                rows.append(([j.strip() for j in c[0].split('/')], [x.strip() for x in c[1].split('/')],
                             c[4] if len(c) > 4 else ''))
    return rows


def split():
    os.makedirs(TL, exist_ok=True)
    bs, dups = plan()
    nm = names()
    gl = glossary()
    for i, b in enumerate(bs):
        rows, text = [], ''
        for e in b:
            sp = (nm.get(e['speaker']) or nm.get(e['speaker'] + ':', '').rstrip(':') or e['speaker']) or '-'
            jp = e['jp'].rstrip(SPACE).replace('\n', ' / ')
            rows.append('%s\t%s\t%s\t%s\t%s' % (e['id'], sp, e['kind'], limit_text(e['kind']), jp))
            text += e['jp'] + e['speaker']
        with open(os.path.join(TL, bname(i) + '.tsv'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(rows) + '\n')
        terms = [r for r in gl if any(len(j) >= 1 and j in text for j in r[0])]
        with open(os.path.join(TL, 'terms_%s.txt' % bname(i)), 'w', encoding='utf-8', newline='\n') as f:
            for r in terms:
                f.write('%s = %s%s\n' % (' / '.join(r[0]), ' / '.join(r[1]), '  (avoid: %s)' % r[2] if r[2] else ''))
    with open(os.path.join(TL, 'dups.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dups, f, indent=0)
    with open(os.path.join(TL, 'plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({bname(i): [e['id'] for e in b] for i, b in enumerate(bs)}, f, indent=0)
    print('split %d batches (%d unique entries, %d repeats) into %s' % (
        len(bs), sum(len(b) for b in bs), len(dups), TL))


def frozen():
    """Batch membership fixed at split time (work/tl/plan.json), so later fixes don't shift batches."""
    with open(os.path.join(TL, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def batch_entries(batch):
    byid = {e['id']: e for f, ents in load_dlg() for e in ents}
    return [byid[i] for i in frozen()[batch]]


def read_out(batch):
    p = os.path.join(TL, batch + '.out.tsv')
    if not os.path.exists(p):
        return None
    out = {}
    for line in open(p, encoding='utf-8-sig').read().splitlines():
        if not line.strip():
            continue
        if '\t' not in line:
            out.setdefault('__bad__', []).append(line[:40])
            continue
        i, en = line.split('\t', 1)
        out[i.strip()] = en.replace('\\n', '\n').strip()
    return out


def check_entry(e, en, gl):
    errs, warns = [], []
    if not en:
        return ['empty'], warns
    if JP_RE.search(en):
        errs.append('Japanese/fullwidth left in English')
    if '\t' in en or '\\u' in en:
        errs.append('tab or \\u escape')
    bad = enc.check_text(en)
    if bad:
        errs.append('characters the font lacks: %r' % ''.join(bad))
    if errs:
        return errs, warns
    kind = e['kind']
    w, n = layout.LIMITS[kind]
    if kind == 'msg':
        pages = layout.pages(kind, en)
        lines = [ln for pg in pages for ln in pg]
        if max(enc.line_halves(x) for x in lines) > w:
            errs.append('a word longer than the box (%d)' % w)
        jp_boxes = 1
        if len(pages) > jp_boxes + 1:
            warns.append('%d boxes for one Japanese box' % len(pages))
        if len(lines) > 1 and len(lines[-1]) < 6 and len(en) > 30:
            warns.append('stub last line %r' % lines[-1])
    else:
        if '\n' in en:
            errs.append('no line breaks allowed here')
        elif enc.line_halves(en) > w:
            errs.append('too long: %d > %d chars' % (enc.line_halves(en), w))
    src = e['jp'] + e['speaker']
    for jps, ens, avoid in gl:
        for a in [x.strip() for x in avoid.split(',') if x.strip()]:
            if re.search(r'\b' + re.escape(a) + r'\b', en):
                errs.append('avoided spelling %r' % a)
        if any(len(j) >= 2 and j in e['jp'] for j in jps) and not any(x.lower() in en.lower() for x in ens):
            warns.append('glossary: %s -> %s not found' % ('/'.join(jps), ' / '.join(ens)))
    return errs, warns


def check(batch, quiet=False):
    data = batch_entries(batch)
    out = read_out(batch)
    if out is None:
        print('%s: no output file work/tl/%s.out.tsv' % (batch, batch))
        return False
    gl = glossary()
    ids = [e['id'] for e in data]
    bad = 0
    for x in out.get('__bad__', []):
        print('  line without a tab:', x)
        bad += 1
    missing = [i for i in ids if i not in out]
    extra = [i for i in out if i not in ids and i != '__bad__']
    if missing:
        print('  missing ids:', ', '.join(missing[:20]), '...' if len(missing) > 20 else '')
        bad += len(missing)
    if extra:
        print('  unknown ids:', ', '.join(extra[:20]))
        bad += len(extra)
    nwarn = 0
    for e in data:
        if e['id'] not in out:
            continue
        errs, warns = check_entry(e, out[e['id']], gl)
        for x in errs:
            print('  %s: %s' % (e['id'], x))
        bad += len(errs)
        if not quiet:
            for wn in warns:
                print('  warn %s: %s' % (e['id'], wn))
        nwarn += len(warns)
    print('%s: %s%s' % (batch, 'OK' if not bad else '%d error(s)' % bad, ', %d warning(s)' % nwarn if nwarn else ''))
    return bad == 0


def write_en(updates, status):
    """updates {id: en}: write into the dlg files, plus every repeat of those ids."""
    dups = json.load(open(os.path.join(TL, 'dups.json'), encoding='utf-8')) if os.path.exists(
        os.path.join(TL, 'dups.json')) else plan()[1]
    full = dict(updates)
    for d, first in dups.items():
        if first in updates:
            full[d] = updates[first]
    n = 0
    for f, ents in load_dlg():
        changed = False
        for e in ents:
            if e['id'] in full:
                e['en'] = full[e['id']]
                e['status'] = status
                changed = True
                n += 1
        if changed:
            with open(f, 'w', encoding='utf-8', newline='\n') as fh:
                json.dump(ents, fh, ensure_ascii=False, indent=1)
                fh.write('\n')
    return n


def merge(batch):
    if not check(batch, quiet=True):
        return False
    out = read_out(batch)
    out.pop('__bad__', None)
    n = write_en(out, 'tl')
    print('merged %s (%d entries incl. repeats)' % (batch, n))
    return True


def fix(path):
    fixes = {}
    for line in open(path, encoding='utf-8-sig').read().splitlines():
        if line.strip():
            i, en = line.split('\t', 1)
            fixes[i.strip()] = en.replace('\\n', '\n').strip()
    gl = glossary()
    byid = {e['id']: e for f, ents in load_dlg() for e in ents}
    ok = {}
    for i, en in fixes.items():
        if i not in byid:
            print('  unknown id', i)
            continue
        errs, _ = check_entry(byid[i], en, gl)
        if errs:
            print('  %s: %s' % (i, errs))
            continue
        ok[i] = en
    n = write_en(ok, 'reviewed')
    print('fixed %d of %d (%d entries incl. repeats)' % (len(ok), len(fixes), n))
    return len(ok) == len(fixes)


def main():
    a = sys.argv[1:]
    if not a or a[0] == 'list':
        byid = {e['id']: e for f, ents in load_dlg() for e in ents}
        tot = 0
        for b, ids in frozen().items():
            done = sum(1 for i in ids if byid[i].get('en'))
            tot += done
            print('%s: %d entries, %d translated' % (b, len(ids), done))
        allv = [e for e in byid.values() if not skip(e)]
        print('dialogue: %d/%d entries have English' % (sum(1 for e in allv if e.get('en')), len(allv)))
        return 0
    if a[0] == 'split':
        split()
        return 0
    if a[0] == 'check':
        return 0 if check(a[1]) else 1
    if a[0] == 'merge':
        return 0 if merge(a[1]) else 1
    if a[0] == 'fix':
        return 0 if fix(a[1]) else 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
