"""Dialogue font: 2048 glyphs, 16x16 4bpp (4 tiles: TL, TR, BL, BR), 12 px used horizontally.
Table at ROM 0xEDB7C4: u32 pointer per high byte (0..7). Glyph code c -> block[c>>8] + ((c>>4)&15)*0x80 + (c&15)*0x800.
Renderer: 0x080518B0 (code, dest, odd) draws the left 12 px of the glyph."""
FONT_TABLE = 0xEDB7C4
FONT_BASE = 0x31AEB4          # block 0; blocks are 0x8000 apart (contiguous up to 0x35AEB4)
NGLYPHS = 2048


def glyph_off(code):
    return FONT_BASE + (code >> 8) * 0x8000 + ((code >> 4) & 15) * 0x80 + (code & 15) * 0x800


def glyph_pixels(rom, code):
    """16x16 list of rows of 4-bit values."""
    g = rom[glyph_off(code):glyph_off(code) + 0x80]
    px = [[0] * 16 for _ in range(16)]
    for t in range(4):
        tx, ty = (t % 2) * 8, (t // 2) * 8
        for r in range(8):
            for c in range(8):
                b = g[t * 32 + r * 4 + c // 2]
                px[ty + r][tx + c] = (b >> ((c & 1) * 4)) & 15
    return px


def encode_glyph(px):
    """Inverse of glyph_pixels: 16x16 rows of 4-bit values -> 0x80 bytes."""
    out = bytearray(0x80)
    for t in range(4):
        tx, ty = (t % 2) * 8, (t // 2) * 8
        for r in range(8):
            for c in range(0, 8, 2):
                out[t * 32 + r * 4 + c // 2] = px[ty + r][tx + c] | (px[ty + r][tx + c + 1] << 4)
    return bytes(out)
