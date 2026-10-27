# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** done (all phases); release zip rebuilt 2026-10-27 after the visual-QA gate passed.
- **Done:** dialogue 8188/8188, bank 2383, names, items/equipment, menus (glyph cache patch tools/menuasm.py), all
  graphics text (title, act cards, battle labels tools/labels.py, demo captions tools/captions.py, shop signs
  tools/signs.py; see docs/re/graphics.md). Repo restructured to fan-translation-template (2026-10-27: subagent
  types, docs/screenshots; D9).
- **Visual-QA gate 2026-10-27** (skill phase 8/9): tour of every script on EN (work/qa/tour) and JP reference
  (identity build, work/qa/tour_jp); stalled chains finished as <group>x groups (`tour.py rest`); 272 sheets in
  work/qa/manifest.tsv, verdicts in work/qa/verdicts from read-only reviewers (docs/visual-qa-brief.md);
  release.py now runs `qa_gate.py check`. After a rebuild: re-run changed groups, `qa_gate.py init`, prune
  manifest lines whose sheet is gone, review `todo` chunks. Fixed from 3 review rounds:
  - tools/layout.py: every wrapped message evens its lines (no one-word last line); long messages are packed a
    sentence per page where that costs no extra box (507 -> 318 mid-sentence page ends, the rest are sentences
    longer than a box); a title ("Mr.") never ends a line. Self-test in check.py.
  - Scan line drew 14 codes, cutting 3-code weaknesses ("Weak: Scen"): build.py patches 0x08053BE0 to 15.
  - "Junk Kid gang!" space (B0006), 巫面 = Kannagi mask everywhere (glossary), "Got Maria's Bracelet!", leading
    "?" lines -> "Huh? ...", と・に・か・く = "A-ny-way!".
  - Not reached: F48380/F49654 hang the chain (skipped by the plan's f031x/f033x, as before). f031's karaoke
    scripts 11-25 wait for a random NPC: reached and reviewed in round 2 (work/qa/tour_r2/f031), not in round 3
    (no karaoke text changed since). Battle chains stall in the command menu with layout-dependent timing;
    their scripts are covered by the x groups.
- **Agent playtest 2026-10-23** (docs/playtester-brief.md; sessions work/playtest/s_*, s2_*), fixed:
  - 74 map NPC/door scripts never started (flagged pointers 0x88../0x18.. in 0xB0000-0xBF000 not repointed; black
    screen on talking to Anzu, story stuck). tests.py now checks every script pointer.
  - Field main menu garbled after any sub-screen (glyph cache stayed on).
  - Battle/status text: name pad gaps, scan Type/Weak line, Has-Been Fighter tag, Venom Fang label space,
    Electromagnetic Scan/Field in the status list, M/W 7 px wide ("Ma" read "Mb"), several reworded lines.
  - Checked as original behaviour (same on JP): main-street shop doors shut early in Act 1, save-screen TIME
    position, status stat rows touching.
  - Item list names ran under the count (count 10 tiles after the name, 0x0800DB76): 55 names shortened to
    12 halves (D8), items_check limit 12; squid is "H-Face Squid" in menu and drop message.
- **Open bugs:**
  - Bank B0112/B0114 still "Electro Scan/Field" (lint cap 16 from JP length; where the bank copy is drawn is unknown).
- **Not playtested yet:** past Act 1 "ask around" (no trigger found), equipment with gear, shops, Run line at battle start.
- **Published 2026-10-27:** github.com/minhnhattonthat/getbackers-dakkanya-jagan-fuuin-en, release v1.1 (patch SHA-1 e162276f…). Title BG map now rebuilt from the user's ROM (tools/gfx.py title_vram); the Konami dumps tbl/gfx/title.*.bin were removed from history before the first push.
