"""Shared text helpers: glyph table, PAC3 script parsing.

PAC3 script = b'PAC3' then records [u32 size][payload size bytes] ... until a payload starting ffffffff
(a size-0 record is an empty text line). Payload whose first u32 has its top nibble 8..B = command (op word + args);
anything else = text: u16 glyph codes (0..0x7FF), see docs/re/text.md."""
import os
import re
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM_JP = os.path.join(ROOT, 'rom', 'GetBackers Dakkanya - Jagan Fuuin! (Japan).gba')


def load_rom(path=ROM_JP):
    with open(path, 'rb') as f:
        return f.read()


def load_glyphs():
    """code -> char from tbl/glyphs.txt (sheet reading order)."""
    rows = []
    blk = None
    table = {}
    with open(os.path.join(ROOT, 'tbl', 'glyphs.txt'), encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('## block'):
                blk = int(line.split()[-1]); rows = []
                continue
            if not line or line.startswith('#'):
                continue
            assert len(line) == 16, (blk, line)
            r = len(rows)
            rows.append(line)
            for c, ch in enumerate(line):
                n = r * 16 + c
                code = blk * 256 + (n % 16) * 16 + n // 16
                table[code] = ch
    return table


def is_cmd(payload):
    return len(payload) >= 4 and (struct.unpack_from('<I', payload)[0] >> 28) in (8, 9, 0xA, 0xB)


def find_scripts(rom):
    """Offsets of every PAC3 script in the script area."""
    return [m.start() for m in re.finditer(b'PAC3', rom) if m.start() % 4 == 0 and m.start() >= 0xE00000]


def parse_script(rom, off):
    """-> (records, end). records: list of (offset_of_size_word, payload bytes)."""
    assert rom[off:off + 4] == b'PAC3'
    q = off + 4
    recs = []
    while True:
        n = struct.unpack_from('<I', rom, q)[0]
        if n == 0xFFFFFFFF:          # the string bank at 0xFB6034 ends at the 0xFF fill, no terminator record
            return recs, q
        assert n < 0x1000 and n % 2 == 0, 'bad record size %x at %x' % (n, q)
        pay = rom[q + 4:q + 4 + n]
        recs.append((q, pay))
        q += 4 + n
        if pay[:4] == b'\xff\xff\xff\xff':
            return recs, q


def codes_of(payload):
    return list(struct.unpack_from('<%dH' % (len(payload) // 2), payload))


def decode(codes, table):
    return ''.join(table.get(c, '[%03X]' % c) for c in codes)
