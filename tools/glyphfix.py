"""Correct a misread glyph in tbl/glyphs.txt, located by context.
usage: python -X utf8 tools/glyphfix.py CONTEXT INDEX NEWCHAR [--dry]
  CONTEXT: a Japanese substring as currently decoded (e.g. 文勾), INDEX: position of the wrong char in it.
Finds the glyph code behind that character in the script text, prints all its other uses, and rewrites
that code's cell in tbl/glyphs.txt (then re-run tools/extract.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT, load_rom, load_glyphs, find_scripts, parse_script, is_cmd, codes_of, decode  # noqa: E402


def main():
    ctx, idx, new = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    rom = load_rom()
    t = load_glyphs()
    codes = set()
    uses = []
    for s in find_scripts(rom):
        for q, p in parse_script(rom, s)[0]:
            if not p or is_cmd(p):
                continue
            cs = codes_of(p)
            d = [t.get(c, '?') for c in cs]
            txt = ''.join(d)
            k = txt.find(ctx)
            while k >= 0:
                codes.add(cs[k + idx])
                k = txt.find(ctx, k + 1)
    if len(codes) != 1:
        raise SystemExit('context matches codes %s' % [hex(c) for c in codes])
    code = codes.pop()
    for s in find_scripts(rom):
        for q, p in parse_script(rom, s)[0]:
            if p and not is_cmd(p):
                cs = codes_of(p)
                if code in cs:
                    uses.append(decode(cs, t))
    print('code %03X (%s) used %d times, e.g.: %s' % (code, t[code], len(uses), ' | '.join(u[:20] for u in uses[:6])))
    if '--dry' in sys.argv:
        return
    blk, mid, lo = code >> 8, (code >> 4) & 15, code & 15
    path = os.path.join(ROOT, 'tbl', 'glyphs.txt')
    lines = open(path, encoding='utf-8').read().split('\n')
    b = None
    r = 0
    for i, l in enumerate(lines):
        if l.startswith('## block'):
            b, r = int(l.split()[-1]), 0
            continue
        if not l or l.startswith('#'):
            continue
        if b == blk and r == lo:
            assert l[mid] == t[code]
            lines[i] = l[:mid] + new + l[mid + 1:]
            break
        r += 1
    open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('set %03X to %s' % (code, new))


if __name__ == '__main__':
    main()
