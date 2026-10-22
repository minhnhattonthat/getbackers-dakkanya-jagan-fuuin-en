# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** done (all phases); v1.1 release zip in release/ is STALE (built before the 2026-10-23 playtest fixes):
  rebuild with `build.py release` before publishing.
- **Done:** dialogue 8188/8188, bank 2383, names, items/equipment, menus (glyph cache patch tools/menuasm.py), all
  graphics text (title, act cards, battle labels tools/labels.py, demo captions tools/captions.py, shop signs
  tools/signs.py; see docs/re/graphics.md). Phase 8 tour: 69 field + 11 battle groups viewed; clean battle captures
  per group in work/qa/tour/b0NNc/clean.png. Repo restructured to fan-translation-template (2026-10-23).
- **Agent playtest 2026-10-23** (docs/playtester-brief.md; sessions work/playtest/s_*, s2_*), fixed:
  - 74 map NPC/door scripts never started (flagged pointers 0x88../0x18.. in 0xB0000-0xBF000 not repointed; black
    screen on talking to Anzu, story stuck). tests.py now checks every script pointer.
  - Field main menu garbled after any sub-screen (glyph cache stayed on).
  - Battle/status text: name pad gaps, scan Type/Weak line, Has-Been Fighter tag, Venom Fang label space,
    Electromagnetic Scan/Field in the status list, M/W 7 px wide ("Ma" read "Mb"), several reworded lines.
  - Checked as original behaviour (same on JP): main-street shop doors shut early in Act 1, save-screen TIME
    position, status stat rows touching.
- **Open bugs:**
  - Item list: the count column starts ~12 halves after the name (two columns, `adds r4,#0xa` at 0x0800DB76,
    slots 0x080B0464); 55 of 346 item names are longer and run under the count ("Human-Face Sq02").
    items_check.py's limit of 16 is wrong. Needs a user decision (shorten vs re-layout).
  - Same item, two names: bank B0222 "Man-Face Squid" (drop message) vs items.json "Human-Face Squid".
  - Bank B0112/B0114 still "Electro Scan/Field" (lint cap 16 from JP length; where the bank copy is drawn is unknown).
- **Not playtested yet:** past Act 1 "ask around" (no trigger found), equipment with gear, shops, Run line at battle start.
- **Waiting on the user:** item-name decision; publishing.
