# Graphics text survey

| Where | Data | Status |
|---|---|---|
| Title logo 奪還屋 box / 邪眼封印！ strip | BG2 8bpp tiles at 0x8505C (map rebuilt from the ROM by tools/gfx.py title_vram) | English ("DAKKANYA", "EVIL EYE SEALED!"), tools/gfx.py |
| Katakana ゲットバッカーズ above the logo | same BG | painted out (tools/gfx.py TITLE_EDITS) |
| Title copyright line | OBJ strip at 0x1B51A8 | English, tools/gfx.py (proportional font) |
| Act title cards 0-9 | table 0x9BADC (tiles + map), copied to free space with new tiles | English, tools/actcards.py |
| Battle commands, party names, item and skill labels | OBJ sprite resources (table ~0xA60610, 7 words: palette, size, tiles, size, frames, anim, flag); entries 0xA6062C (commands/names/items), 0xA60648 + 0xA60664 (skills) | English, tools/labels.py (sheets copied to 0x1F00000+, numbered labels re-laid 128 px; cost/count tile offsets: table 0x3008B8, literals 0x5AF54/0x5B0B8/0x5B530) |
| Opening demo name captions, 邪 眼 封印 card, title flash | BG strips, entries in the table ~0xA5FE00 (palette, size, tiles, size, map, map size, descriptor) | English, tools/captions.py |
| Shop signs in field maps | LZ77 tile sets of the field map table 0x1B34AC (7 words: size, palette, tiles, 3 layers, 0) | English, tools/signs.py + tools/signs.json (sheet rectangles; street signs as map cells harvested from VRAM dumps) |
| Takoyaki sign たこるん (Honky Tonk street) | tiles shared with the rest of the sign | kana erased, octopus kept |
| Dot-pattern pseudo text on posters / narrow vertical signs, tatami scribble | map tiles | left (not legible text) |

Notes
- Field map layer data is not a plain tile map (VRAM entries differ); sign cells were read from BG2 VRAM dumps,
  with the BG scroll found by matching the screenshot (work/qa/scroll.py approach: equal-neighbour pattern).
- Battle label piece tile numbers are 16-bit: new tiles must lie within 2 MiB after the sheet base.
