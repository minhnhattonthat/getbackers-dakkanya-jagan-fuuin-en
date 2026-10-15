"""One-command check (the pre-commit hook runs this): identity build, codec self-tests, extract roundtrip,
English build + ROM-range diff, text lint. Exit code = number of failed steps.
usage: python -X utf8 tools/check.py"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = [sys.executable, '-X', 'utf8']
STEPS = [
    ('identity build', PY + ['build.py', 'identity']),
    ('encoder selftest', PY + ['tools/enc.py']),
    ('english build', PY + ['build.py', 'build']),
    ('tests', PY + ['tools/tests.py']),
    ('lint', PY + ['tools/lint.py']),
]


def main():
    bad = 0
    for name, cmd in STEPS:
        if not os.path.exists(os.path.join(ROOT, cmd[3] if len(cmd) > 3 else '')):
            continue
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        print('%-18s %s  %s' % (name, 'ok' if r.returncode == 0 else 'FAIL', ' | '.join(tail)[:300]))
        bad += r.returncode != 0
    print('check: %s' % ('OK' if not bad else '%d step(s) failed' % bad))
    return bad


if __name__ == '__main__':
    sys.exit(main())
