"""Tests: script coverage (every text record of every script belongs to an extracted entry), JSON integrity,
romdiff of the English build (writes only inside allowed ranges).
usage: python -X utf8 tools/tests.py"""
import glob
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlib import ROOT, load_rom, load_glyphs, find_scripts, parse_script, is_cmd  # noqa: E402
from extract import messages, BANK  # noqa: E402
import fontlib  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def test_coverage(rom, t):
    ids = set()
    for f in glob.glob(os.path.join(ROOT, 'script', 'dlg', '*.json')):
        for e in json.load(open(f, encoding='utf-8')):
            check(e['id'] not in ids, 'duplicate id ' + e['id'])
            ids.add(e['id'])
    names = {e['jp'] for e in json.load(open(os.path.join(ROOT, 'script', 'names.json'), encoding='utf-8'))}
    for s in find_scripts(rom):
        if s == BANK:
            continue
        recs, _ = parse_script(rom, s)
        covered = set()
        for n, u in enumerate(messages(rom, s, t)):
            covered.update(u['recs'])
            if u['kind'] in ('name', 'bname'):
                check(u['jp'].rstrip('　') in names, 'name missing %s' % u['jp'])
            else:
                check('%06X:%d' % (s, n) in ids, 'entry missing %06X:%d' % (s, n))
        for i, (q, p) in enumerate(recs):
            if p and not is_cmd(p) and p[:4] != b'\xff\xff\xff\xff':
                check(i in covered, 'text record not covered at %X' % q)


def test_romdiff(rom):
    path = os.path.join(ROOT, 'build', 'getbackers_en.gba')
    if not os.path.exists(path):
        return
    new = open(path, 'rb').read()
    allowed = [(fontlib.FONT_BASE, fontlib.FONT_BASE + 8 * 0x8000), (0xEE1AC4, 0xFE0000), (0x1000000, 0x2000000)]
    # pointer words the build repoints
    for lo, hi in [(0, 0xB0000), (0xED0000, 0xEE1AC4)]:
        for i in range(lo, hi, 4):
            v = struct.unpack_from('<I', rom, i)[0]
            if 0x08EE1AC4 <= v < 0x08FC2618:
                allowed.append((i, i + 4))
    allowed.append((0x58174, 0x58178))
    allowed.append((0xFE4000, 0xFFF000))      # menu data
    import sysmenu
    import items
    allowed += items.allowed()
    for scr in sysmenu.load():
        for d in scr.get('digits', []):
            allowed.append((int(d, 16), int(d, 16) + 20))
        for k, n in (('charset_lit', 4), ('charset_imm', 1)):
            a = int(scr[k], 16)
            allowed.append((a, a + n))
        for lab in scr['labels']:
            for k, n in (('lit', 4), ('imm', 1)):
                for x in str(lab.get(k) or '').split(','):
                    if x:
                        a = int(x, 16)
                        allowed.append((a, a + n))
    extra = os.path.join(ROOT, 'tools', 'allowed_ranges.txt')
    if os.path.exists(extra):
        for line in open(extra, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                a, b = line.split('-')
                allowed.append((int(a, 16), int(b, 16)))
    allowed.sort()
    starts = [a for a, b in allowed]
    import bisect

    def ok(i):
        k = bisect.bisect_right(starts, i) - 1
        return any(allowed[j][0] <= i < allowed[j][1] for j in range(max(0, k - 2), k + 1))
    n = min(len(rom), len(new))
    bad = []
    for c in range(0, n, 0x1000):
        if rom[c:c + 0x1000] == new[c:c + 0x1000]:
            continue
        if any(a <= c and c + 0x1000 <= b for a, b in allowed[:3]):
            continue
        for i in range(c, min(c + 0x1000, n)):
            if rom[i] != new[i] and not ok(i):
                bad.append(i)
                break
        if len(bad) > 5:
            break
    check(not bad, 'romdiff: bytes changed outside allowed ranges at ' + ', '.join('%X' % b for b in bad))


def main():
    rom = load_rom()
    t = load_glyphs()
    t[0x5C3] = '　'
    test_coverage(rom, t)
    test_romdiff(rom)
    for f in fails[:20]:
        print('FAIL', f)
    print('tests: %d failure(s)' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
