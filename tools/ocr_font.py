"""Guess the character of every kanji glyph (codes 0x100-0x7FF) by matching against Windows Japanese fonts,
and draw review sheets (game glyph | guess) so a human/agent can correct the guesses by eye.
Block 0 (codes 0x00-0xFF: ASCII, kana, punctuation) is transcribed by hand in tools/jp_block0.txt.
Glyph order: reading index n inside a 256-glyph block -> code = blk*256 + (n%16)*16 + n//16.
usage: python -X utf8 tools/ocr_font.py ROM          -> work/ocr.tsv, work/ocr_<blk>.png"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, __file__.replace('\\', '/').rsplit('/', 1)[0])
from fontlib import glyph_pixels

S, SIG = 20, 1.0
FONTS = [('C:/Windows/Fonts/msgothic.ttc', 16, 0), ('C:/Windows/Fonts/msgothic.ttc', 15, 0),
         ('C:/Windows/Fonts/YuGothM.ttc', 16, 0), ('C:/Windows/Fonts/msgothic.ttc', 20, 0)]


def kanji_cands():
    out = []
    for hi in list(range(0x88, 0xA0)) + list(range(0xE0, 0xEB)):
        for lo in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            try:
                ch = bytes([hi, lo]).decode('cp932')
            except UnicodeDecodeError:
                continue
            if '\u4e00' <= ch <= '\u9fff':
                out.append(ch)
    return out + ['々', '〆', 'ヶ']


def feat(a):
    ys, xs = np.nonzero(a > 0.4)
    crop = Image.fromarray((a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] * 255).astype(np.uint8))
    crop = crop.resize((S, S), Image.BILINEAR).filter(ImageFilter.GaussianBlur(SIG))
    v = np.asarray(crop, dtype=np.float32).ravel()
    v = v - v.mean()
    return v / (np.linalg.norm(v) or 1)


def code_of(blk, n):
    return blk * 256 + (n % 16) * 16 + n // 16


def main():
    rom = open(sys.argv[1], 'rb').read()
    cands = kanji_cands()
    mats = []
    for path, size, idx in FONTS:
        f = ImageFont.truetype(path, size, index=idx)
        vs = []
        for ch in cands:
            img = Image.new('L', (40, 40), 0)
            ImageDraw.Draw(img).text((2, 2), ch, font=f, fill=255)
            vs.append(feat(np.asarray(img, dtype=np.float32) / 255))
        mats.append(np.stack(vs))
    rows = {}
    for blk in range(1, 8):
        for n in range(256):
            code = code_of(blk, n)
            a = (np.array(glyph_pixels(rom, code)) >= 3).astype(np.float32)
            if not a.any():
                rows[code] = ('', [])
                continue
            g = feat(a)
            s = sum(m @ g for m in mats) / len(mats)
            top = np.argsort(-s)[:5]
            rows[code] = (cands[top[0]], [(cands[i], float(s[i])) for i in top])
    with open('work/ocr.tsv', 'w', encoding='utf-8', newline='\n') as f:
        for code in sorted(rows):
            ch, top = rows[code]
            f.write('%03X\t%s\t%s\n' % (code, ch, ' '.join('%s%.2f' % t for t in top)))
    # review sheets: per glyph a cell with the game glyph (left) and the guess (right), 16 per row
    gf = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 30)
    sf = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 16)
    for blk in range(1, 8):
        for half in range(2):
            img = Image.new('RGB', (16 * 96, 8 * 56), (40, 40, 40))
            d = ImageDraw.Draw(img)
            for n in range(half * 128, half * 128 + 128):
                code = code_of(blk, n)
                x0, y0 = (n % 16) * 96, (n // 16 - half * 8) * 56
                px = glyph_pixels(rom, code)
                for y in range(16):
                    for x in range(13):
                        if px[y][x] == 3:
                            d.rectangle([x0 + 2 + x * 3, y0 + 3 + y * 3, x0 + 4 + x * 3, y0 + 5 + y * 3], fill=(255, 255, 255))
                d.text((x0 + 44, y0 + 2), rows[code][0], font=gf, fill=(255, 220, 80))
                d.text((x0 + 44, y0 + 36), ''.join(c for c, _ in rows[code][1][1:4]), font=sf, fill=(150, 200, 255))
                d.line([x0 + 95, y0, x0 + 95, y0 + 55], fill=(90, 90, 90))
            img.save('work/ocr_%d%s.png' % (blk, 'ab'[half]))
    print('wrote work/ocr.tsv and work/ocr_<blk><a|b>.png')


if __name__ == '__main__':
    main()
