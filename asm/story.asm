; Story font (11px) proportional advance. put-glyph (0x08081010) draws each glyph as its own OBJ and moved the
; cursor by font width + 1 (12 px). For the story font the hook takes the advance from a per-code byte table
; (tools/insert.py: English cells end where their ink ends, {name} letters are proportional), so a run after a
; colour code, {name} or {word1} continues right where the previous one stopped. Other fonts keep width + 1.
; Included by menu8.asm (same armips run). ADV_TABLE / ADV_COUNT come from tools/insert.py.

STORY_FONT equ 0x080D6C24
STORY_CODE equ 0x0809C800      ; end of the zero gap, after the menu8 code

; ldrh r0,[r3] / adds r0,#1 / ldr r1,[r5,#0x10] / ldrh r1,[r1] / adds r0,r1,r0 / strh r0,[r3] (12 bytes)
.org 0x0808107E
  ldr r0,=adv_hook+1
  bx r0
.pool

.org STORY_CODE
; r3 = &cursor x, r5 = text object, [sp + 4] = glyph code (the caller's r5, saved by put-glyph's push)
adv_hook:
  ldr r1,[r5,#0x10]
  ldr r0,=STORY_FONT
  cmp r0,r1
  bne @@pitch
  ldr r0,[sp,#4]
  ldr r2,=ADV_COUNT
  cmp r0,r2
  bhs @@pitch
  ldr r2,=ADV_TABLE
  ldrb r0,[r2,r0]
  b @@add
@@pitch:
  ldrh r0,[r1]
  add r0,#1
@@add:
  ldrh r1,[r3]
  add r0,r1,r0
  strh r0,[r3]
  ldr r1,=0x0808108B
  bx r1
.pool
.if . > 0x0809C8C0
  .error "story code overflows the gap"
.endif
