# Text

## Font (dialogue, menus, battle)
- 2048 glyphs, u16 codes 0x000-0x7FF. Table at 0xEDB7C4: u32 per high byte (blocks 0..7 = 0x0831AEB4 + n*0x8000).
- Glyph = 16x16 4bpp (tiles TL,TR,BL,BR), 0x80 bytes; colours: 0 transparent, 3 ink, 2 anti-alias. Only the left
  12 px x 15 rows are used; the renderer (0x080518B0, called with code/dest/odd) packs 2 glyphs into 3 tiles.
- Code c -> offset block[c>>8] + ((c>>4)&15)*0x80 + (c&15)*0x800 (the sheet is 16 glyphs wide; reading index
  n in a block -> code (n%16)*16 + n//16). Block 0 = punctuation, ASCII, kana; blocks 1-7 = kanji in order of
  first appearance. `tbl/glyphs.txt` is the transcription (by eye; `tools/ocr_font.py` made the review sheets).
- 0x5C3 = full-width space (also used as padding); empty slots 0x6AE, 0x708-0x7FF partly.
- English: digraph glyphs (two 6 px letters per 12 px cell) written over codes 0x100-0x7FF at build time
  (`tools/enc.py`); block 0 is kept because code prints digits from it.

## PAC3 scripts (2018 + string bank)
- `PAC3` then records `[u32 size][payload]`. Payload first u32 with top nibble 8-B = command; otherwise text
  (u16 codes, size multiple of 4, padded with 0x5C3). A size-0 record = empty text line. Script ends with a
  payload `FFFFFFFF FFFFFFFF`, then 4 zero bytes before the next PAC3.
- Scripts are linear (no internal offsets). 0xEE1AC4-0xFB6030, every one followed by 4 zero bytes.
- Text-bearing commands: 80000008 slot + name; 8000000A + 1 line; 8000000B + 2 lines; 8000000C count,x,y,w,h
  + N options (choice window in 8 px tiles); A0000001 + prompt line; 9F000004 / A0000002 + battle name ("名:")
  + line. 9000xxxx = sprite/effect ops, A0000000 n = wait, B000000x = script type (first record).
- References: absolute u32 pointers in code literal pools (0x0-0xB0000) and tables 0xED0000-0xEE1AC4
  (e.g. battle cut-in table 0xEDB9F0). 31 scripts have no pointer: they are reached by walking on from the
  previous script, so the build repacks all scripts contiguously in the original order and repoints every pointer.
- Start: 0x0804C3B4 start_script(r0 = PAC3 ptr), current pointer kept at 0x0201B998; 0x0804C338 validates the
  type (B000000x).

## String bank 0xFB6034-0xFC2618 (PAC3 header, 2383 text records, no terminator)
- Only pointer: literal 0x08058174 (code 0x0805814C) walks 0x94E records at boot into a RAM table 0x02024F14
  (8 bytes each: ptr, length). Length = size/2, minus one trailing 0x5C3. Records must stay 4-byte aligned (ldm).
- Contents: battle messages (fragments appended to names: "は毒をうけた！"), skill names, sound-test and
  gallery captions, character full names, enemy names...

## System strings 0xAC1D0-0xAE6FC
- Menu "charsets": glyph-code lists rendered once into VRAM; labels elsewhere are u16 index lists into them
  (0xA57D4.., terminated 0xFFFF). Item table 0xAE7D0: 16-byte records [name idx list, ?, description, icon].
  Descriptions are raw codes without terminator. To do: RE before translating.
