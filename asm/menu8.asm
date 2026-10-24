; 8x8 menu font: condensed pair codes drawn through a run-time tile cache.
; Text codes 0x4000-0x63FF are two characters: 0x4000 + (a-0x20)*0x60 + (b-0x20) (0x200+ and 0x2000-0x200F
; are palette codes in some drawers). Each drawer that turns a
; code into a BG map entry calls conv first; conv puts the pair's tile into a free font slot (the Japanese kana /
; kanji tiles, list in pool.bin) of the font copy in VRAM and returns that slot's code, so the drawer's own
; base/palette arithmetic is unchanged. One code is still one tile: no layout code changes.
; Assembled by tools/insert.py with armips onto the built ROM. Docs: docs/re/menu8.md.

.gba
.open BUILD_ROM, 0x08000000
.thumb

RAM       equ 0x0203F000          ; zero in every screen sampled (menu, map, battle, intro, story)
FONTADDR  equ RAM                 ; u32: VRAM address of font tile 0, 0 = unknown
COUNTER   equ RAM + 4             ; u32: LRU clock
CODES     equ RAM + 8             ; u16[POOL_MAX]: pair code held by each slot (0 = empty)
AGES      equ RAM + 0x200         ; u32[POOL_MAX]: last use
FONT_SIG  equ 0x080BEDF0 + 0x0C * 32   ; ROM font tile for 'A' (code 0x0C): never overwritten in VRAM

; ---- hooks: each replaces 4 bytes with a bl to its stub ----
.org 0x08027E1C :: bl stub_r3_strh      ; draw0 (0x08027DE8): adds r0,r3,r0 / strh r0,[r1]
.org 0x08027F58 :: bl stub_r3_strh      ; draw (0x08027F1C)
.org 0x08027EE8 :: bl stub_r1_r3_strh4  ; typewriter (shop dialogue): adds r0,r1,r3 / strh r0,[r4]
.org 0x08027FC0 :: bl stub_ip_strh      ; draw (0x08027F78): add r0,ip / strh r0,[r1]
.org 0x0802803C :: bl stub_r5_strh      ; draw (0x08027FF8): adds r0,r5,r0 / strh r0,[r1]
.org 0x0803D178 :: bl stub_ip_orr5      ; line drawer (0x0803D114): add r0,ip / orrs r0,r5
.org 0x0803D1F6 :: bl stub_ldrh_r6      ; line drawer, wrapped: ldrh r0,[r0] / adds r0,r6,r0
.org 0x0803D306 :: bl stub_pal_r0       ; renderer (0x0803D29C): ldr r0,=0x1FF / cmp r2,r0 (then bhi = palette)
.org 0x0803D31A :: bl stub_ldrh_r4      ; renderer: ldrh r4,[r4] / adds r0,r4,r2
.org 0x0803D3B2 :: bl stub_pal_r4       ; renderer, wrapped: ldr r4,=0x1FF / cmp r2,r4
.org 0x0803D3C6 :: bl stub_ldrh_r5      ; renderer, wrapped: ldrh r5,[r5] / adds r0,r5,r2
.org 0x0803DE48 :: bl stub_ldrh_ip1e    ; popup drawer (Home Base party menu): ldrh r0,[r0] / ldrh r3,[r3,#0x1e]
; world map stage box "%s\n%s%c%s": the colon (code 0xE6) after "Mission" is now in the label (a pair tile, so no
; half-tile gap); the %c becomes a space
.org 0x08084A64 :: mov r0,#1
; fusion cost prompt: the "G" after the price (1 code of 0BD48A) is skipped; m8 0BD852 starts with the pair "G."
; so the price reads "20G. That suit you?" with no half-tile gap
.org 0x0805CD06 :: mov r2,#0
; monster stat box glyph plotters (9px 0x080628D8, 11px 0x080629E4) start at glyph column 1 (JP glyphs never
; ink column 0); English VWF cells do, so start at column 0
.org 0x08062906 :: mov r5,#0
.org 0x08062A12 :: mov r5,#0
; sprite text: single glyph tiles copied from the ROM font at font + code*32 (r0 = code << 5)
.org 0x0801C788 :: bl tile_r0           ; ldr r1,=font / adds r0,r0,r1
.org 0x0801F6B2 :: bl tile_r0
.org 0x0807EBD2 :: bl tile_r0           ; world map labels
.org 0x08082B0C :: bl tile_r0
.org 0x08064BDC :: bl tile_r3           ; ldr r0,=font / adds r0,r3,r0 (r3 = code << 5)
.org 0x0800DEA6 :: bl tile_dma_r3       ; battle unit panel (name, element): lsls r0,r3,#5 / adds r0,r0,r2 (r2 = font)
; window text module (0x0807CB34, world map labels): lsls r0,#12 / orrs r0,r5 (r5 = code)
.org 0x0807CBA4 :: bl stub_win

; Code must be within bl range (4 MB) of the hooks: the zero gap 0x0809C3F0-0x0809C8D0 after the program code
; (no pointer into it; never read in boot/story/menu/map/battle tours).
CODE_START equ 0x0809C400
CODE_END   equ 0x0809C800      ; 0x0809C800-0x0809C8C0: story.asm
.org CODE_START
stub_r3_strh:
  push {lr}
  bl conv
  add r0,r3,r0
  strh r0,[r1]
  pop {pc}

stub_r1_r3_strh4:
  push {lr}
  mov r0,r1
  bl conv
  add r0,r0,r3
  strh r0,[r4]
  pop {pc}

stub_ip_strh:
  push {lr}
  bl conv
  add r0,r12
  strh r0,[r1]
  pop {pc}

stub_r5_strh:
  push {lr}
  bl conv
  add r0,r5,r0
  strh r0,[r1]
  pop {pc}

stub_ip_orr5:
  push {lr}
  bl conv
  add r0,r12
  orr r0,r5
  pop {pc}

stub_ldrh_r6:
  push {lr}
  ldrh r0,[r0]
  bl conv
  add r0,r6,r0
  pop {pc}

stub_ldrh_r4:
  push {lr}
  ldrh r4,[r4]
  mov r0,r2
  bl conv
  add r0,r4,r0
  pop {pc}

stub_ldrh_r5:
  push {lr}
  ldrh r5,[r5]
  mov r0,r2
  bl conv
  add r0,r5,r0
  pop {pc}

stub_ldrh_ip1e:
  push {lr}
  ldrh r0,[r0]
  bl conv
  ldrh r3,[r3,#0x1e]
  pop {pc}

stub_win:
  push {lr}
  lsl r0,r0,#12
  push {r0}
  mov r0,r5
  bl conv
  pop {r2}
  orr r0,r2
  pop {pc}

; r0 = code << 5 -> r0 = source tile address (pair table for pair codes, else the ROM font); r1 = font
tile_r0:
  ldr r1,=0x80000
  cmp r0,r1
  blo @@font
  ldr r1,=pairs - 0x80000
  add r0,r0,r1
  ldr r1,=0x080BEDF0
  bx lr
@@font:
  ldr r1,=0x080BEDF0
  add r0,r0,r1
  bx lr

tile_r3:
  ldr r0,=0x80000
  cmp r3,r0
  blo @@font
  ldr r0,=pairs - 0x80000
  add r0,r3,r0
  bx lr
@@font:
  ldr r0,=0x080BEDF0
  add r0,r3,r0
  bx lr

; r3 = code, r2 = font -> r0 = source tile address. Keeps r1 (DMA base).
tile_dma_r3:
  lsl r0,r3,#5
  push {r1}
  ldr r1,=0x80000
  cmp r0,r1
  blo @@font
  ldr r1,=pairs - 0x80000
  b @@add
@@font:
  mov r1,r2
@@add:
  add r0,r0,r1
  pop {r1}
  bx lr

; palette test: codes 0x200-0xFFF are palette changes (bhi taken); pair codes 0x1000+ are glyphs (not taken)
stub_pal_r0:
  ldr r0,=0xFFF
  cmp r2,r0
  bhi @@big
  ldr r0,=0x1FF
  cmp r2,r0
  bx lr
@@big:
  ldr r0,=0x1FF
  cmp r2,r2
  bx lr

stub_pal_r4:
  ldr r4,=0xFFF
  cmp r2,r4
  bhi @@big
  ldr r4,=0x1FF
  cmp r2,r4
  bx lr
@@big:
  ldr r4,=0x1FF
  cmp r2,r2
  bx lr

; ---- conv: r0 = code -> r0 = code to draw. Preserves r1-r12. ----
conv:
  push {r1-r7,lr}
  mov r4,r0
  lsr r1,r4,#12
  cmp r1,#4
  blo @@ret
  cmp r1,#6
  bhi @@ret
  bl locate
  cmp r5,#0
  beq @@ret
  ldr r7,=CODES
  ldr r3,=pool
  ldrh r2,[r3]                    ; slot count
  mov r1,#0
@@search:
  cmp r1,r2
  bhs @@miss
  lsl r0,r1,#1
  ldrh r0,[r7,r0]
  cmp r0,r4
  beq @@have
  add r1,#1
  b @@search
@@miss:                           ; least recently used slot (empty slots have age 0)
  ldr r3,=AGES
  mov r1,#0
  ldr r6,[r3]
  mov r0,#1
@@lru:
  cmp r0,r2
  bhs @@take
  lsl r7,r0,#2
  ldr r7,[r3,r7]
  cmp r7,r6
  bhs @@next
  mov r6,r7
  mov r1,r0
@@next:
  add r0,#1
  b @@lru
@@take:
  ldr r7,=CODES
  lsl r0,r1,#1
  strh r4,[r7,r0]
@@have:                           ; r1 = slot index: make sure VRAM holds the pair (font reloads wipe it)
  ldr r3,=pool + 2
  lsl r0,r1,#1
  ldrh r7,[r3,r0]                 ; slot's tile code
  ldr r6,=pairs - 0x80000
  lsl r0,r4,#5
  add r4,r6,r0                    ; src tile
  bl put_tile
  ldr r3,=COUNTER
  ldr r0,[r3]
  add r0,#1
  str r0,[r3]
  ldr r3,=AGES
  lsl r2,r1,#2
  str r0,[r3,r2]
  mov r0,r7
  pop {r1-r7,pc}
@@ret:
  mov r0,r4
  pop {r1-r7,pc}

; ---- locate: r5 = VRAM address of font tile 0 (0 if the font is not in BG VRAM). Keeps r4. ----
; Screens can hold a stale font copy (the map keeps the menu's at 0x06004000 under its picture), so first try the
; char bases of the enabled BGs, BG3 (text layer) first, then the last hit, then a scan.
locate:
  push {lr}
  ldr r6,=FONT_SIG
  ldr r7,=FONTADDR
  mov r1,#3
@@bg:
  ldr r0,=0x04000000
  ldrh r2,[r0]                    ; DISPCNT
  mov r3,r1
  add r3,#8
  lsr r2,r3
  lsl r2,r2,#31
  beq @@nextbg                    ; BG off
  lsl r3,r1,#1
  add r3,#8
  ldrh r2,[r0,r3]                 ; BGxCNT
  lsl r2,r2,#28
  lsr r2,r2,#30                   ; char base block
  lsl r5,r2,#14
  ldr r0,=0x06000000
  add r5,r5,r0
  push {r1}
  bl check
  pop {r1}
  beq @@found
@@nextbg:
  sub r1,#1
  bpl @@bg
  ldr r5,[r7]
  cmp r5,#0
  beq @@scan
  bl check
  beq @@done
@@scan:
  ldr r5,=0x06000000
@@loop:
  bl check
  beq @@found
  add r5,#32
  ldr r0,=0x06010000 - 0x180
  cmp r5,r0
  blo @@loop
  mov r5,#0
@@found:
  str r5,[r7]
@@done:
  pop {pc}

; ---- put_tile: r4 = src tile, r7 = tile code -> written into the font copy of every enabled BG (the world map
; draws its labels from char block 1 while BG2/3 hold another copy at block 0), else at r5. Uses r0-r6. ----
put_tile:
  push {r1,lr}
  push {r5}                       ; fallback, dropped once a BG copy is written
  ldr r6,=FONT_SIG
  mov r1,#3
@@bg:
  ldr r0,=0x04000000
  ldrh r2,[r0]                    ; DISPCNT
  mov r3,r1
  add r3,#8
  lsr r2,r3
  lsl r2,r2,#31
  beq @@next                      ; BG off
  lsl r3,r1,#1
  add r3,#8
  ldrh r2,[r0,r3]                 ; BGxCNT
  lsl r2,r2,#28
  lsr r2,r2,#30                   ; char base block
  lsl r5,r2,#14
  ldr r0,=0x06000000
  add r5,r5,r0
  push {r1}
  bl check
  pop {r1}
  bne @@next
  bl copy32
  mov r0,#0
  str r0,[sp]
@@next:
  sub r1,#1
  bpl @@bg
  pop {r5}
  cmp r5,#0
  beq @@out
  bl copy32
@@out:
  pop {r1,pc}

; copy the 32-byte tile r4 to font r5 slot r7, writing only changed words. Uses r0, r2, r3, r5.
copy32:
  lsl r0,r7,#5
  add r3,r5,r0
  mov r2,#0
@@c:
  ldr r0,[r4,r2]
  ldr r5,[r3,r2]
  cmp r0,r5
  beq @@s
  str r0,[r3,r2]
@@s:
  add r2,#4
  cmp r2,#32
  blo @@c
  bx lr

; Z set when the 32 bytes at r5 + 0x180 equal FONT_SIG (r6). Uses r0-r3.
check:
  mov r1,#0xC0
  lsl r1,r1,#1
  add r1,r5,r1
  mov r2,#0
@@c:
  ldr r0,[r6,r2]
  ldr r3,[r1,r2]
  cmp r0,r3
  bne @@out
  add r2,#4
  cmp r2,#32
  blo @@c
  cmp r2,r2
@@out:
  bx lr

.pool
.if . > CODE_END
  .error "menu8 code overflows the gap"
.endif

.include "story.asm"

.org MENU8_DATA
.align 4
pool:
.incbin POOL_BIN
.align 4
pairs:
.incbin PAIRS_BIN

.close
