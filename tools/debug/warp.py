"""Cold-boot warp: python -X utf8 tools/debug/warp.py SCENE [--rom R] [--out DIR] [--frames N] [--after ROUTE]
       [--mash N] [--shot-every N] [--state-out S] [--sheet]
SCENE: a name from tools/debug/scenes.json, or a raw spec:
  title | newgame | script:<ORIG_OFFSET_HEX>   (plays that PAC3 script in place of the Act 1 intro; the build's
  .map.json gives its address in the built ROM)
`all` warps every scene in scenes.json into work/qa/warp/<name>/ and saves work/states/<name>.mss."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path(r'H:\translation\batch\.claude\skills\translate-retro-game')
ORIG = ROOT / 'rom' / 'GetBackers Dakkanya - Jagan Fuuin! (Japan).gba'
SCENES = json.loads((ROOT / 'tools' / 'debug' / 'scenes.json').read_text(encoding='utf-8'))


def target_addr(rom, off):
    m = Path(str(rom) + '.map.json')
    if m.exists():
        return json.loads(m.read_text(encoding='utf-8'))['scripts'][off.upper()]
    return 0x08000000 + int(off, 16)     # original ROM: scripts are where extract found them


def cmd_for(name, a):
    s = SCENES.get(name, {'spec': name})
    spec = s['spec']
    out = Path(a.out or ROOT / 'work' / 'qa' / 'warp' / name.replace(':', '_'))
    cmd = [sys.executable, '-X', 'utf8', str(SKILL / 'scripts' / 'emu.py'), str(a.rom), '--out', str(out),
           '--script', str(ROOT / 'tools' / 'debug' / 'warp.lua'),
           '--frames', str(a.frames or s.get('frames', 3000)),
           '--shot-every', str(a.shot_every or s.get('shot_every', 60)), '--timeout', '900']
    kind, _, arg = spec.partition(':')
    cmd += ['--var', f"SCENE='{kind}'"]
    if kind == 'script':
        cmd += ['--var', 'TARGET=0x%08X' % target_addr(a.rom, arg)]
    if kind == 'map':
        parts = arg.split(':')
        cmd += ['--var', 'MAP=%d' % int(parts[0])]
        if len(parts) == 3:
            cmd += ['--var', 'MX=%d' % int(parts[1]), '--var', 'MY=%d' % int(parts[2])]
    if s.get('enc'):
        cmd += ['--var', 'ENC=1']
    if s.get('nth'):
        cmd += ['--var', 'NTH=%d' % s['nth']]
    after = a.after or s.get('after')
    if after:
        cmd += ['--var', f"AFTER='{after}'"]
    mash = a.mash or s.get('mash', {'script': 45, 'map': 40}.get(kind, 0))
    if mash:
        cmd += ['--mash', str(mash)]
    for x in a.script or []:
        cmd += ['--script', x]
    for x in a.var or []:
        cmd += ['--var', x]
    state = a.state_out or (ROOT / 'work' / 'states' / f"{name.replace(':', '_')}.mss" if a.save_state else None)
    if state:
        cmd += ['--state-out', str(state)]
    if a.sheet:
        cmd.append('--sheet')
    return cmd, out


def run(name, a):
    cmd, out = cmd_for(name, a)
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    log = (out / 'log.txt').read_text(encoding='utf-8', errors='replace') if (out / 'log.txt').exists() else ''
    ok = r.returncode == 0 and 'ARRIVED' in log
    print(f"{name}: {'ok' if ok else 'FAIL rc=%d' % r.returncode} ({out})")
    return ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument('scene')
    p.add_argument('--rom', default=str(ORIG))
    p.add_argument('--out')
    p.add_argument('--frames', type=int)
    p.add_argument('--after')
    p.add_argument('--mash', type=int)
    p.add_argument('--shot-every', type=int)
    p.add_argument('--state-out')
    p.add_argument('--save-state', action='store_true')
    p.add_argument('--sheet', action='store_true')
    p.add_argument('--script', action='append', help='extra Lua probe(s)')
    p.add_argument('--var', action='append', help='NAME=LUA passed to emu.py')
    a = p.parse_args()
    if a.scene == 'all':
        a.save_state, a.sheet = True, True
        bad = [n for n in SCENES if not run(n, a)]
        print('failed:', bad or 'none')
        return 1 if bad else 0
    return 0 if run(a.scene, a) else 1


if __name__ == '__main__':
    sys.exit(main())
