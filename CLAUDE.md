# GetBackers Dakkanya - Jagan Fuuin! (GBA) English translation

Skill: translate-retro-game (H:\translation\batch\.claude\skills\translate-retro-game\SKILL.md). Read it before ROM, text or QA work. `$SKILL` = that dir.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py build` -> build/getbackers_en.gba (`identity` = JP rebuild == original, `marker` = id+filler build, `build ID=text ..` -> build/getbackers_qa.gba)
- Check:    `python -X utf8 tools/check.py` (identity, enc selftest, English build, tests incl. romdiff, lint; the pre-commit hook runs it)
- Smoke:    `python -X utf8 H:/translation/batch/.claude/skills/translate-retro-game/scripts/emu.py build/getbackers_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 tools/debug/warp.py SCENE [--rom build/getbackers_en.gba] [--sheet]` (SCENE = name in tools/debug/scenes.json, or `script:<orig offset>` = play any PAC3 script from a cold boot in place of the Act 1 intro; `newgame`, `title`). Never ask the user to play to a scene.
- Text:     `tools/extract.py` (never clobbers en), `tools/batches.py split|check|merge`, `tools/fit.py`
- Release:  `python -X utf8 build.py release` (never publish without the user)

## Paths
- Original ROM: `rom/GetBackers Dakkanya - Jagan Fuuin! (Japan).gba` (gitignored; SHA-1 8c9e6900e537d8d1909b3e4b512f8fbd3ff92712). Emulator: `tools/mesen/` (MesenCE 2.2.1, github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip + Firmware/gba_bios.bin via fetch_emu.py gba-bios; gitignored).
- Text: `script/dlg/dNN.json` (PAC3 messages), `script/bank.json` (string bank), `script/names.json` (speaker tags). Glyph table: `tbl/glyphs.txt`; English font `tbl/font_en.txt`. Glossary + rulings: `glossary.md`. RE notes: `docs/re/README.md`.

## Rulings (pre-approved by the user)
- Edit source files only with the file-edit tool. Full names, no abbreviations (engine work first). Honorifics dropped; given name first. Romanization: official English (Tokyopop/anime) > Hepburn. Credits in English. Graphics text in scope.
- Never push/publish/upload. Release = local `release/getbackers-dakkanya-jagan-fuuin_en.zip` (patch + README).
- Engine: English = digraph glyphs (2 letters per 12 px cell) allocated at build time into font codes 0x100-0x7FF; messages auto-paginate (extra 0B boxes); scripts repacked contiguously (order matters).

## Status
- Done: all phases. Dialogue 8188/8188, bank 2383, names, items/equipment, menus (glyph cache patch tools/menuasm.py), all graphics text (title, act cards, battle labels tools/labels.py, demo captions tools/captions.py, shop signs tools/signs.py; see docs/re/graphics.md). ROM grows to 32 MiB (label sheets at 0x1F00000+). Phase 8 tour: 69 field + 11 battle groups viewed; clean battle captures per group in work/qa/tour/b0NNc/clean.png. Release v1.1 local.
- Known gaps: takoyaki sign letters (shared tiles) erased only; dot-pattern poster text left. Open bugs: none known.
