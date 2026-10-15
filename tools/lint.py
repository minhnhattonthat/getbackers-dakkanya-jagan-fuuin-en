"""Text lint over everything the build inserts: dialogue, names, bank, items, menus.
Errors: missing English, characters the font lacks, Japanese left, over-wide lines for fixed fields, avoided
spellings, ordinal suffix after a placeholder. Prints errors and a one-line summary; exit 1 on any error."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT  # noqa: E402
import enc  # noqa: E402
import layout  # noqa: E402
import batches  # noqa: E402
import bankbatch  # noqa: E402
import items_check  # noqa: E402
import items  # noqa: E402
import sysmenu  # noqa: E402

errs = []
warns = 0


def err(i, m):
    errs.append('%s: %s' % (i, m))


def common(i, en):
    if batches.JP_RE.search(''.join(c for c in en if c not in enc.FULL)):
        err(i, 'Japanese left')
    bad = enc.check_text(en)
    if bad:
        err(i, 'font lacks %r' % ''.join(bad))
    if re.search(r'\d(st|nd|rd|th)\b', en) and '[' in en:
        err(i, 'ordinal suffix after a variable')


def main():
    global warns
    gl = batches.glossary()
    avoid = [a.strip() for r in gl for a in r[2].split(',') if a.strip()]
    for f, ents in batches.load_dlg():
        for e in ents:
            if batches.skip(e):
                continue
            en = e.get('en', '')
            if not en:
                err(e['id'], 'no English')
                continue
            common(e['id'], en)
            for a in avoid:
                if re.search(r'\b' + re.escape(a) + r'\b', en):
                    err(e['id'], 'avoided spelling %r' % a)
            w, n = layout.LIMITS[e['kind']]
            if e['kind'] == 'msg':
                lines = [ln for pg in layout.pages('msg', en) for ln in pg]
                if max(enc.line_halves(x) for x in lines) > w:
                    err(e['id'], 'word wider than the box')
            elif enc.line_halves(en) > w or '\n' in en:
                err(e['id'], 'too long for %s (%d > %d)' % (e['kind'], enc.line_halves(en), w))
    for e in json.load(open(os.path.join(ROOT, 'script', 'names.json'), encoding='utf-8')):
        if not e.get('en'):
            err('name ' + e['jp'], 'no English')
            continue
        common('name ' + e['jp'], e['en'])
        lim = layout.LIMITS['bname' if e['jp'].endswith(':') else 'name'][0]
        if enc.line_halves(e['en']) > lim:
            err('name ' + e['jp'], 'too long (%d > %d)' % (enc.line_halves(e['en']), lim))
    for e in bankbatch.load():
        if bankbatch.skip(e):
            continue
        if not e.get('en'):
            err(e['id'], 'no English')
            continue
        for m in bankbatch.check_one(e, e['en']):
            err(e['id'], m)
    for e in items.load():
        for m in items_check.check(e):
            err(e['id'], m)
    for scr in sysmenu.load():
        for lab in scr['labels']:
            if not lab.get('en'):
                err('%s %s' % (scr['id'], lab['jp']), 'no English')
            else:
                for line in lab['en'].split('\n'):
                    common('%s %s' % (scr['id'], lab['jp']), line)
    for x in errs[:40]:
        print(x)
    print('lint: %d error(s)%s' % (len(errs), '' if len(errs) <= 40 else ' (first 40 shown)'))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
