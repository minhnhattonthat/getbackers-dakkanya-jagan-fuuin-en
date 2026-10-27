"""Puts the translate-retro-game skill's scripts/ on sys.path (import for the side effect; SCRIPTS for subprocesses).
$SKILL = the directory holding its SKILL.md; default: the Claude Code plugin checkout."""
import os
import sys
from pathlib import Path

SKILL = Path(os.environ.get("SKILL", Path.home() / ".claude/plugins/marketplaces/retro-translation/skills/translate-retro-game"))
SCRIPTS = SKILL / "scripts"
if not SCRIPTS.is_dir():
    sys.exit(f"translate-retro-game skill not found at {SKILL}: install the plugin or set $SKILL")
if str(SCRIPTS) not in sys.path:
    sys.path.insert(1, str(SCRIPTS))  # after tools/, ahead of site-packages, as the old vendored path was

if __name__ == "__main__":
    print(SKILL.as_posix())
