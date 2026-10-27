# Engine notes (script interpreter, battle, debug hooks)

## Script interpreter
- `start_script` 0x0804C3B4: r0 = ROM address of a PAC3 script. It sets the current record pointer
  0x0201B998 (= script + 12) and the script type 0x0201B99C (= u32 at script + 8, low nibble = type).
- Types 0, 1, 2, 6 = field/event scripts; the others are battle cut-in scripts (only draw inside a battle).
- A script ends at a record whose second word is 0xFFFFFFFF.
- Message ops: 80000008 speaker, 8000000A/B one/two-line box, 8000000C choice (count, x, y, w, h in tiles),
  A0000001 prompt line, 9F000004/A0000002 battle speaker + line. Battle boxes are not cleared by the interpreter
  between records; each cut-in script opens a fresh box.

## Maps / encounters
- `load_map` 0x080083C0 (r0 = index into the map table 0x080B31DC, r1/r2 = x/y tile, r3 = facing).
- Encounter counter 0x02000D70 (u8): forcing it to 1 starts a battle on the next step (debug ENC=1).
- Map event tables (0xB0000-0xBF000) hold script pointers with flags in the top nibble: NPC talk scripts
  0x88xxxxxx (copied to the NPC objects, RAM 0x03004798 + 0x88 + idx*0x90, tested by `bge`/`& 0x7FFFFFFF`),
  door/trigger scripts 0x18xxxxxx (table 0x080B78E8 per map, read at trigger time by 0x08006670, `& 0x0FFFFFFF`).
  The script then runs via 0x0805DA50 -> RAM 0x0201B9D0 -> start_script. **verified** (breakpoints, JP vs EN).
  build.py repoints them keeping the flag; tests.py checks every script pointer lands on a PAC3 header.

## String bank
- 0xFB6034-0xFC2618, 2383 records, walked at boot by 0x0805814C (literal pool 0x08058174) into the RAM table
  0x02024F14 (8 bytes each). Records must stay 4-byte aligned.
- Scan line (0x08053BC0): memcpy (0x0808142C) of template B0039 into 0x0201EB44, then type name (B0040+) at code 3
  and weakness at code 12, each by its record length; drawn as a fixed 14 codes (movs r0,#0xE at 0x08053BE0).
  build.py makes it 15 so a 3-code weakness ("Sc|en|t ") shows in full.

## Menu charset system and glyph-cache patch
- 0x0800FA2C loads a screen charset; 0x0800FAAC draws a label by length; 0x0800FB60 draws an
  FFFF-terminated list (FFFE = newline); 0x0800FC88 draws digits through index lists.
- tools/menuasm.py hooks 0x0800FA2E / 0x0800FAE0 / 0x0800FB9A through trampolines stored in font glyph 0x7FF;
  cache RAM 0x0203FE00, 240 slots; label descriptor FFFD, k, prefill. Glyph 0x6AE = blank filler (reserved).
  The main menu is a plain charset at the same tile base as the cache sub-screens and is redrawn after them, so a
  plain load at the cache's tile0 turns the cache off (else its index lists read as glyph codes: kana garbage).

## Debug harness (tools/debug)
- warp.lua replaces the NTH script start after NEW GAME (scene `script:<off>`), loads any map (`map:IDX[:X:Y]`),
  or chains many scripts in one boot (`chain:` + CHAIN_END=1: at each end record the interpreter is pointed at
  the next target). Battle-script tours: scene battle_act1 (map 2 + ENC=1), NTH=6 = first battle script start.
- tour.py: plan/run/status; contact sheets in work/qa/tour/<group>/sheet_NN.png.
