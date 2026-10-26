# GetBackers Dakkanya - Jagan Fuuin! (GBA) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md; tools find it via `tools/skill.py`, `$SKILL` env var overrides the plugin path). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py build` -> build/getbackers_en.gba (checks the dump against `rom.sha1` first; `identity` = JP rebuild == original, `marker` = id+filler build, `build ID=text ..` -> build/getbackers_qa.gba)
- Check:    `python -X utf8 tools/check.py` (identity, enc selftest, English build, tests incl. romdiff, lint; the pre-commit hook runs it)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/getbackers_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 tools/debug/warp.py SCENE [--rom build/getbackers_en.gba] [--sheet]` (SCENE = name in tools/debug/scenes.json, or `script:<orig offset>` = play any PAC3 script from a cold boot in place of the Act 1 intro; `newgame`, `title`). Never ask the user to play to a scene.
- Text:     `tools/extract.py` (never clobbers en), `tools/batches.py split|check|merge`, `tools/fit.py`
- Release:  `python -X utf8 build.py release` (gate + BPS + zip; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/GetBackers Dakkanya - Jagan Fuuin! (Japan).gba` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1, github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip + Firmware/gba_bios.bin via fetch_emu.py gba-bios; gitignored). Savestates: `work/states/`.
- Text: `script/dlg/dNN.json` (PAC3 messages), `script/bank.json` (string bank), `script/names.json` (speaker tags). Glyph table: `tbl/glyphs.txt`; English font `tbl/font_en.txt`. Glossary: `glossary.md`. Briefs: `docs/*-brief.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- Engine: English = digraph glyphs (2 letters per 12 px cell) allocated at build time into font codes 0x100-0x7FF; messages auto-paginate (extra 0B boxes); scripts repacked contiguously (order matters). ROM grows to 32 MiB (label sheets at 0x1F00000+).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
