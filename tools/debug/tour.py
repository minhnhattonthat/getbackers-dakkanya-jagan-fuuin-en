"""QA tour of every PAC3 script with text: chains of scripts from cold boots, a screenshot before each A press,
one contact sheet per chain cropped to the message area (work/qa/tour/<group>/sheet_*.png).
  python -X utf8 tools/debug/tour.py plan                 -> work/qa/tour/plan.json (groups of 25)
  python -X utf8 tools/debug/tour.py run [--jobs 3] [--only g000,g001] [--rom build/getbackers_en.gba]
  python -X utf8 tools/debug/tour.py status               -> which groups ran, which scripts played
Script types 0/1/2/6 play in the Act 1 intro context; battle types 3/4/5 need a battle (see battle_act1)."""
import argparse
import json
import os
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from textlib import load_rom, find_scripts, parse_script, is_cmd  # noqa: E402

TOUR = ROOT / 'work' / 'qa' / 'tour'
SKILL = Path(r'H:\translation\batch\.claude\skills\translate-retro-game')
PER = 25
FIELD_TYPES = (0, 1, 2, 6)


def plan():
    rom = load_rom()
    groups = {'field': [], 'battle': []}
    for s in sorted(find_scripts(rom)):
        if s == 0xFB6034:
            continue
        recs, _ = parse_script(rom, s)
        if not any(p and not is_cmd(p) and p[:4] != b'\xff' * 4 for q, p in recs):
            continue
        ty = struct.unpack_from('<I', recs[0][1])[0] & 0xF
        groups['field' if ty in FIELD_TYPES else 'battle'].append('%06X' % s)
    out = {}
    for kind, ss in groups.items():
        for i in range(0, len(ss), PER):
            out['%s%03d' % (kind[0], i // PER)] = ss[i:i + PER]
    TOUR.mkdir(parents=True, exist_ok=True)
    (TOUR / 'plan.json').write_text(json.dumps(out, indent=0), encoding='utf-8')
    print('groups', len(out), {k: len(v) for k, v in groups.items()})


def run_group(name, ss, rom):
    out = TOUR / name
    if (out / 'log.txt').exists() and 'CHAIN DONE' in (out / 'log.txt').read_text(encoding='utf-8', errors='replace'):
        return name, 'cached'
    cmd = [sys.executable, '-X', 'utf8', str(ROOT / 'tools' / 'debug' / 'warp.py'), 'chain:' + ','.join(ss),
           '--rom', rom, '--out', str(out), '--frames', str(4000 + 1600 * len(ss)), '--shot-every', '100000',
           '--mash', '40', '--var', 'CHAIN_END=1', '--var', 'MSHOT=1']
    if name.startswith('b'):
        cmd[4] = 'chain:' + ','.join(ss)
    subprocess.run(cmd, cwd=ROOT, capture_output=True)
    shots = sorted(out.glob('m*.png'))
    for i in range(0, len(shots), 42):
        subprocess.run([sys.executable, '-X', 'utf8', str(SKILL / 'scripts' / 'sheet.py')] +
                       [str(p) for p in shots[i:i + 42]] +
                       ['--crop', '0,88,240,72', '--div', '1', '--cols', '3', '--max', '42', '--changed', '0.004',
                        '--out', str(out / ('sheet_%02d.png' % (i // 42)))], cwd=ROOT, capture_output=True)
    log = (out / 'log.txt').read_text(encoding='utf-8', errors='replace') if (out / 'log.txt').exists() else ''
    return name, '%d played%s' % (log.count('PLAY '), ', done' if 'CHAIN DONE' in log else '')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['plan', 'run', 'status'])
    p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--only')
    p.add_argument('--rom', default=str(ROOT / 'build' / 'getbackers_en.gba'))
    a = p.parse_args()
    if a.cmd == 'plan':
        plan()
        return 0
    pl = json.loads((TOUR / 'plan.json').read_text(encoding='utf-8'))
    names = a.only.split(',') if a.only else [n for n in pl if n.startswith('f')]
    if a.cmd == 'status':
        for n in names:
            lg = TOUR / n / 'log.txt'
            t = lg.read_text(encoding='utf-8', errors='replace') if lg.exists() else ''
            print(n, len(pl[n]), 'played', t.count('PLAY '), 'done' if 'CHAIN DONE' in t else '')
        return 0
    with ThreadPoolExecutor(a.jobs) as ex:
        for name, res in ex.map(lambda n: run_group(n, pl[n], a.rom), names):
            print(name, res, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
