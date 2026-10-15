"""Check script/items.json English (limits in docs/items-brief.md). usage: python -X utf8 tools/items_check.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enc  # noqa: E402
import items  # noqa: E402
import batches  # noqa: E402


def check(e):
    errs = []
    lim = 16
    for k in ('name_en', 'text_en'):
        v = e.get(k, '')
        if not v:
            errs.append('%s empty' % k)
            continue
        if batches.JP_RE.search(v):
            errs.append('%s: Japanese left' % k)
        bad = enc.check_text(v)
        if bad:
            errs.append('%s: characters the font lacks %r' % (k, ''.join(bad)))
    if errs:
        return errs
    if enc.line_halves(e['name_en']) > lim:
        errs.append('name_en longer than %d' % lim)
    lines = e['text_en'].split('\n')
    if any(enc.line_halves(x) > 36 for x in lines):
        errs.append('text_en line longer than 36')
    if sum(enc.cell_width(x) for x in lines) > items.TEXT_CELLS:
        errs.append('text_en longer than 72 characters in total')
    return errs


def main():
    bad = 0
    for e in items.load():
        for x in check(e):
            print('  %s: %s' % (e['id'], x))
            bad += 1
    print('items: %s' % ('OK' if not bad else '%d error(s)' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
