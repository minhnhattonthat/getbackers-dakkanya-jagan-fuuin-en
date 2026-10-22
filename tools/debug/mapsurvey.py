"""Map graphics survey: warp to every map (map:IDX), dump VRAM after arrival, keep each distinct BG tile set.
    python -X utf8 tools/debug/mapsurvey.py run [--jobs 3] [--rom build/getbackers_en.gba]
    python -X utf8 tools/debug/mapsurvey.py sheets      -> work/qa/maps/set_NN.png (one per distinct tile set)
Used to find text drawn into map tiles (shop signs)."""
import argparse
import glob
import hashlib
import os
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'work', 'qa', 'maps')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from skill import SKILL  # noqa: E402
TABLE = 0xB31DC


def maps(rom):
    d = open(rom, 'rb').read()
    seen, out = set(), []
    i = 0
    while d[TABLE + i * 32 + 20:TABLE + i * 32 + 21] == b'M':
        nm = d[TABLE + i * 32 + 20:TABLE + i * 32 + 24]
        if nm not in seen:
            seen.add(nm)
            out.append((i, nm.decode()))
        i += 1
    return out


def run_one(idx, name, rom):
    out = os.path.join(OUT, '%03d_%s' % (idx, name))
    if glob.glob(os.path.join(out, 'ppu_*.vram.bin')):
        return name, 'cached'
    cmd = [sys.executable, '-X', 'utf8', os.path.join(ROOT, 'tools', 'debug', 'warp.py'), 'map:%d' % idx,
           '--rom', rom, '--out', out, '--frames', '7400', '--shot-every', '7399',
           '--script', os.path.join(SKILL, 'scripts', 'lua', 'probes', 'ppudump.lua')]
    subprocess.run(cmd, cwd=ROOT, capture_output=True)
    return name, 'ok' if glob.glob(os.path.join(out, 'ppu_*.vram.bin')) else 'FAIL'


def sheets():
    from PIL import Image
    sets = {}
    for vr in sorted(glob.glob(os.path.join(OUT, '*', 'ppu_*.vram.bin'))):
        v = open(vr, 'rb').read()
        io = open(vr.replace('.vram.', '.io.'), 'rb').read()
        disp = struct.unpack_from('<H', io, 0)[0]
        for b in range(4):
            if not disp & (0x100 << b):
                continue
            c = struct.unpack_from('<H', io, 8 + 2 * b)[0]
            base = ((c >> 2) & 3) * 0x4000
            blk = v[base:base + 0x4000]
            h = hashlib.md5(blk).hexdigest()
            sets.setdefault(h, (blk, []))[1].append(os.path.basename(os.path.dirname(vr)) + ':BG%d' % b)
    for k, (h, (blk, users)) in enumerate(sorted(sets.items())):
        im = Image.new('L', (32 * 9, 16 * 9 + 12), 64)
        for t in range(512):
            for r in range(8):
                for c in range(8):
                    by = blk[t * 32 + r * 4 + c // 2]
                    p = (by >> 4) if c & 1 else (by & 15)
                    im.putpixel(((t % 32) * 9 + c, 12 + (t // 32) * 9 + r), p * 17)
        im = im.resize((im.width * 2, im.height * 2))
        im.save(os.path.join(OUT, 'set_%02d.png' % k))
        print('set_%02d' % k, ' '.join(users[:6]), '...' if len(users) > 6 else '')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['run', 'sheets'])
    p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--rom', default=os.path.join(ROOT, 'build', 'getbackers_en.gba'))
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.cmd == 'sheets':
        sheets()
        return 0
    with ThreadPoolExecutor(a.jobs) as ex:
        for name, res in ex.map(lambda m: run_one(m[0], m[1], a.rom), maps(a.rom)):
            print(name, res, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
