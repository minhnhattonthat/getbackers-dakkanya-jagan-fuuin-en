"""Dry-run fitter: show how English wraps in a box.
usage: python -X utf8 tools/fit.py "English text" [--kind msg|choice|prompt|bline|name|bname|bank]"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enc  # noqa: E402
import layout  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('text')
    p.add_argument('--kind', default='msg', choices=sorted(layout.LIMITS))
    a = p.parse_args()
    bad = enc.check_text(a.text)
    if bad:
        print('characters the font lacks:', ''.join(bad))
        return 1
    w, n = layout.LIMITS[a.kind]
    if a.kind == 'msg':
        for i, pg in enumerate(layout.pages('msg', a.text)):
            print('box %d:' % (i + 1))
            for ln in pg:
                print('  |%-*s| %d' % (w, ln, enc.line_halves(ln)))
        return 0
    k = enc.line_halves(a.text)
    print('|%s| %d/%d %s' % (a.text, k, w, 'OK' if k <= w else 'TOO LONG'))
    return 0 if k <= w else 1


if __name__ == '__main__':
    sys.exit(main())
