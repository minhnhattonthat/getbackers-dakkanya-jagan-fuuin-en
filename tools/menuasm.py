"""Glyph-cache patch for the charset menus (docs/re/menus.md).

English menu labels need far more distinct 12 px cells than the Japanese charsets (one glyph per kana), so screens
switched to "cache mode" keep label lists as GLYPH CODES and load each glyph into VRAM on first use:
- 0x0800FA2C load_charset(list, bytes, tile0): if list[0] == 0xFFFD (a cache descriptor: FFFD, k, k codes), it
  sets up a cache of bytes/2 slots at tile0 (slots 0..k-1 pre-filled, never evicted: digits drawn by index) and
  loads nothing else. Any other list: original behaviour, and the cache is turned off if the list loads at its
  tile0 (else the main menu, a plain screen redrawn there after a cache sub-screen, read its indices as codes).
- 0x0800FAAC draw_label / 0x0800FB60 draw_label_ff: each entry e becomes the slot holding glyph code e when the
  label's base tile is the cache's tile0 (round-robin eviction from slot k). Other labels: original behaviour.
Cache state lives at RAM 0x0203FE00 (unused EWRAM). Hooks reach the code through trampolines inside the empty
glyph 0x7FF (BL range is 4 MiB)."""
import struct

import keystone

RAM = 0x0203FE00
TRAMP_CODE = 0x7FF          # empty glyph whose 128 bytes hold the trampolines (encoder must not allocate it)
FONT_TABLE = 0x08EDB7C4
SITES = {'charset': 0x0800FA2E, 'faac': 0x0800FAE0, 'fb60': 0x0800FB9A}
ORIG = {'charset': bytes.fromhex('4f464646'), 'faac': bytes.fromhex('03889804030c'),
        'fb60': bytes.fromhex('03889804030c')}

ASM = r"""
    b hook_charset
    b hook_faac
    b hook_fb60
    nop
hook_charset:
    mov r7, sb
    mov r6, r8
    ldrh r3, [r0]
    ldr r4, =0xFFFD
    cmp r3, r4
    bne hc_ret
    push {r0, r2, lr}
    ldr r5, =RAM
    strh r2, [r5, #2]
    lsrs r3, r1, #1
    strh r3, [r5, #4]
    ldrh r3, [r0, #2]
    strh r3, [r5, #6]
    strh r3, [r5, #8]
    movs r3, #0
    strh r3, [r5, #0]
    ldr r4, =0xFFFF
    movs r3, #0
hc_clr:
    lsls r1, r3, #1
    adds r1, r1, r5
    strh r4, [r1, #0x10]
    adds r3, #1
    cmp r3, #240
    blt hc_clr
    movs r3, #0
hc_pre:
    ldrh r1, [r5, #8]
    cmp r3, r1
    bge hc_done
    lsls r1, r3, #1
    adds r1, r1, r0
    ldrh r1, [r1, #4]
    lsls r2, r3, #1
    adds r2, r2, r5
    strh r1, [r2, #0x10]
    push {r0, r3}
    mov r0, r1
    mov r1, r3
    bl load_slot
    pop {r0, r3}
    adds r3, #1
    b hc_pre
hc_done:
    movs r3, #1
    strh r3, [r5, #0]
    pop {r0, r2}
    movs r1, #0
    pop {r3}
    bx r3
hc_ret:
    @ a plain charset over the cache's tiles (main menu after a sub-screen) turns the cache off
    ldr r4, =RAM
    ldrh r3, [r4, #2]
    cmp r3, r2
    bne hc_out
    movs r3, #0
    strh r3, [r4, #0]
hc_out:
    bx lr

@ r0 = glyph code, r1 = slot; DMA the glyph into tile0 + slot*4. Clobbers r0-r4.
load_slot:
    ldr r4, =FONT_TABLE
    lsrs r2, r0, #8
    lsls r2, r2, #2
    ldr r2, [r4, r2]
    lsls r3, r0, #28
    lsrs r3, r3, #17
    adds r2, r2, r3
    lsls r3, r0, #24
    lsrs r3, r3, #28
    lsls r3, r3, #7
    adds r2, r2, r3
    ldr r4, =RAM
    ldrh r3, [r4, #2]
    lsls r1, r1, #2
    adds r3, r3, r1
    lsls r3, r3, #5
    ldr r1, =0x06008000
    adds r3, r3, r1
    ldr r4, =0x040000D4
    str r2, [r4]
    str r3, [r4, #4]
    ldr r1, =0x80000040
    str r1, [r4, #8]
    ldr r1, [r4, #8]
    bx lr

@ r3 = entry, r1 = label base tile -> r3 = (slot or entry) << 2 (u16). Clobbers r0-r5.
common:
    push {lr}
    ldr r5, =RAM
    ldrh r4, [r5, #0]
    cmp r4, #0
    beq cm_plain
    ldrh r4, [r5, #2]
    lsls r2, r1, #22
    lsrs r2, r2, #22
    cmp r2, r4
    bne cm_plain
    ldrh r4, [r5, #4]
    movs r2, #0
cm_find:
    cmp r2, r4
    bge cm_new
    lsls r0, r2, #1
    adds r0, r0, r5
    ldrh r0, [r0, #0x10]
    cmp r0, r3
    beq cm_hit
    adds r2, #1
    b cm_find
cm_new:
    ldrh r2, [r5, #6]
    adds r0, r2, #1
    cmp r0, r4
    blt cm_nw
    ldrh r0, [r5, #8]
cm_nw:
    strh r0, [r5, #6]
    lsls r0, r2, #1
    adds r0, r0, r5
    strh r3, [r0, #0x10]
    push {r2}
    mov r0, r3
    mov r1, r2
    bl load_slot
    pop {r2}
cm_hit:
    lsls r3, r2, #2
    pop {r0}
    bx r0
cm_plain:
    lsls r3, r3, #18
    lsrs r3, r3, #16
    pop {r0}
    bx r0

hook_faac:
    push {r4-r7, lr}
    ldrh r3, [r0]
    mov r1, sb
    bl common
    pop {r4-r7}
    pop {r0}
    bx r0

hook_fb60:
    push {r1, r4-r7, lr}
    ldrh r3, [r0]
    ldr r1, [sp, #0x2c]
    bl common
    pop {r1, r4-r7}
    pop {r0}
    bx r0
"""


def assemble(addr):
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB)
    src = ASM.replace('=RAM', '=0x%08X' % RAM).replace('=FONT_TABLE', '=0x%08X' % FONT_TABLE)
    src += '\n.ltorg\n'
    enc, _ = ks.asm(src, addr)
    code = bytes(enc)
    # entry points = the branch table at the start of the blob
    syms = {'hook_charset': addr, 'hook_faac': addr + 2, 'hook_fb60': addr + 4}
    return code, syms


def tramp(addr, target):
    """ldr r3,[pc,#0]; bx r3; (pad); .word target|1 at a 4-aligned address."""
    assert addr % 4 == 0
    return struct.pack('<HHI', 0x4B00, 0x4718, target | 1)


def bl(src, dst):
    off = dst - (src + 4)
    assert -0x400000 <= off < 0x400000, 'BL out of range'
    off >>= 1
    hi = 0xF000 | ((off >> 11) & 0x7FF)
    lo = 0xF800 | (off & 0x7FF)
    return struct.pack('<HH', hi, lo)


def apply(rom, code_off, tramp_off):
    """Write the cache code at ROM offset code_off and the trampolines at tramp_off (in the glyph 0x7FF)."""
    for k, a in SITES.items():
        cur = bytes(rom[a - 0x08000000:a - 0x08000000 + len(ORIG[k])])
        assert cur == ORIG[k], 'unexpected bytes at %X' % a
    code, syms = assemble(0x08000000 + code_off)
    rom[code_off:code_off + len(code)] = code
    t = 0x08000000 + tramp_off
    tr = {}
    for i, name in enumerate(('hook_charset', 'hook_faac', 'hook_fb60')):
        ta = t + 8 * i
        rom[ta - 0x08000000:ta - 0x08000000 + 8] = tramp(ta, syms[name])
        tr[name] = ta
    s = SITES['charset']
    rom[s - 0x08000000:s - 0x08000000 + 4] = bl(s, tr['hook_charset'])
    for k, name in (('faac', 'hook_faac'), ('fb60', 'hook_fb60')):
        s = SITES[k]
        rom[s - 0x08000000:s - 0x08000000 + 6] = bl(s, tr[name]) + b'\x00\x00'   # 0000 = movs r0,r0 (nop)
    return len(code)


if __name__ == '__main__':
    code, syms = assemble(0x08FE4000)
    print(len(code), {k: hex(v) for k, v in syms.items()})
