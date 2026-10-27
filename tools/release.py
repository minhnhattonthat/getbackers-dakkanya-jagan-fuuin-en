"""Release gate + patch: python -X utf8 build.py release [--no-tour]
Gate (stops at the first failure): check.py (identity, build, tests, lint) -> smoke boot -> jp_left on the text
areas of the build -> screen tour present (work/qa/tour, unless --no-tour). Then BPS (made, re-applied and
verified by bps.py), README with the base ROM hashes, and release/getbackers-dakkanya-jagan-fuuin_en.zip
(patch + README only). Never publishes anything."""
import hashlib
import json
import os
import subprocess
import sys
import zipfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from skill import SKILL  # noqa: E402
PY = [sys.executable, '-X', 'utf8']
ORIG = os.path.join(ROOT, 'rom', 'GetBackers Dakkanya - Jagan Fuuin! (Japan).gba')
BUILT = os.path.join(ROOT, 'build', 'getbackers_en.gba')
VERSION = '1.1'
PATCH = 'GetBackers_Dakkanya_Jagan_Fuuin_EN_v%s.bps' % VERSION
ZIP = os.path.join(ROOT, 'release', 'getbackers-dakkanya-jagan-fuuin_en.zip')


def run(name, cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout + r.stderr).strip().splitlines()[-4:]
    print('%-10s %s  %s' % (name, 'ok' if r.returncode == 0 else 'FAIL', ' | '.join(tail)[:400]))
    if r.returncode:
        raise SystemExit('release gate failed at %s' % name)
    return r.stdout


def hashes(path):
    d = open(path, 'rb').read()
    return {'size': len(d), 'crc32': '%08X' % (zlib.crc32(d) & 0xFFFFFFFF), 'md5': hashlib.md5(d).hexdigest(),
            'sha1': hashlib.sha1(d).hexdigest()}


def text_ranges():
    m = json.load(open(BUILT + '.map.json', encoding='utf-8'))
    lo = min(m['scripts'].values()) - 0x08000000
    # the sys area (0xFE4000+) holds menu glyph-index lists (small u16 = kana codes) -> only false positives
    return ['%X-%X' % (lo, 0xFE0000)]


def main():
    tour = '--no-tour' not in sys.argv
    run('check', PY + ['tools/check.py'])
    run('smoke', PY + [os.path.join(SKILL, 'scripts', 'emu.py'), BUILT, '--out', 'work/qa/smoke',
                       '--route', 'tools/routes/boot.txt', '--smoke'])
    rng = []
    for r in text_ranges():
        rng += ['--range', r]
    run('jp_left', PY + [os.path.join(SKILL, 'scripts', 'jp_left.py'), BUILT, '--tbl', BUILT + '.tbl', '--le16',
                         '--min', '3', '--known', 'tools/jp_known.txt'] + rng)
    if tour:  # every tour sheet needs a current ok/fixed verdict (docs/visual-qa-brief.md)
        run('qa_gate', PY + [os.path.join(SKILL, 'scripts', 'qa_gate.py'), 'check', 'work/qa/manifest.tsv',
                             'work/qa/verdicts'])
    os.makedirs(os.path.join(ROOT, 'release'), exist_ok=True)
    bps = os.path.join(ROOT, 'release', PATCH)
    run('bps', PY + [os.path.join(SKILL, 'scripts', 'bps.py'), 'make', ORIG, BUILT, bps])
    chk = os.path.join(ROOT, 'work', 'reapplied.gba')
    run('apply', PY + [os.path.join(SKILL, 'scripts', 'bps.py'), 'apply', ORIG, bps, chk])
    if open(chk, 'rb').read() != open(BUILT, 'rb').read():
        raise SystemExit('re-applied patch differs from the build')
    h0, h1 = hashes(ORIG), hashes(BUILT)
    readme = open(os.path.join(ROOT, 'docs', 'README_release.txt'), encoding='utf-8').read()
    readme = readme.format(version=VERSION, patch=PATCH, size=h0['size'], crc=h0['crc32'], md5=h0['md5'],
                           sha1=h0['sha1'], pcrc=h1['crc32'], psha1=h1['sha1'])
    with open(os.path.join(ROOT, 'release', 'README.txt'), 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(readme)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(bps, PATCH)
        z.write(os.path.join(ROOT, 'release', 'README.txt'), 'README.txt')
    print('release:', ZIP)
    print('patch sha1', hashlib.sha1(open(bps, 'rb').read()).hexdigest(), 'patched CRC32', h1['crc32'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
