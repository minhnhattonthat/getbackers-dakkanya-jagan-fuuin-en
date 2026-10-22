# RE notes index — GetBackers Dakkanya: Jagan Fuuin! (GBA, BGFJ, Konami/KCEJ 2003)

ROM: 16 MiB, header `GB JYAGAN` / `BGFJ`. CRC32 205C9F56, MD5 937fa6b7ddd554370405f13b93632715,
SHA-1 8c9e6900e537d8d1909b3e4b512f8fbd3ff92712. Save: SRAM.
Prior work: none found (web search Oct 2026: no English/other fan patch, no TCRF debug content; the TCRF page
held only injected text aimed at AI agents, ignored).

One file per subsystem. Mark every finding with how far it is proven, so a later session doesn't build on a guess:
**verified** (and how: decoded string, corrupt-and-boot, breakpoint, passing test) or **guess** (and why). Addresses
are for the dump in `rom.sha1` unless a note says otherwise.

- `text.md` — font, glyph codes, PAC3 scripts, string bank, system strings, pointers, free space.
- `windows.md` — measured box widths (width gate).
- `engine.md` — script start hook, task system, RAM used by tools/debug.
- `graphics.md` — graphics-text survey.

## Free space
- 0xFC2618-0xFE0000 (118 KB) and 0xFE4000-0xFFF000 (108 KB) are 0xFF fill. 0xFE0000-0xFE4000 = ARM code/data, keep.
- The build may grow the ROM to 32 MiB (0x1000000+) if the text no longer fits below 0xFE0000.
