.nds

.open "VampireData/repack/arm9.bin",0x02000000

; VWF
.org 0x21c23c8
.area 0x2b7,0  ; up to 0x021c2680
  FONT_DATA:
  .import "VampireData/font_data.bin"
  .align

  ; r3 = width in pixels to copy from the font
  ; r4 = the pixel width of the character
  ; r11 = pointer to the current offset in the string (+1)
  VWF_FUNC:
  push {r0-r1}
  ; Go back and look for the character group
  mov r0,r11
  sub r0,r0,1
  @@loop:
  sub r0,r0,1
  ldrb r1,[r0]
  cmp r1,0x90
  blt @@loop
  ; Check that the character group is 0x90
  cmp r1,0x91
  movgt r3,0xa
  movgt r4,0xa
  bgt @@ret
  moveq r3,0x5
  moveq r4,0x8
  beq @@ret
  ; Read the current character and check >= 0x10
  mov r0,r11
  sub r0,r0,1
  ldrb r0,[r0]
  cmp r0,0x10
  movlt r3,0x5
  movlt r4,0x8
  blt @@ret
  ; Get the width and add it
  ldr r1,=FONT_DATA
  add r0,r1,r0
  sub r0,r0,0x10
  ldrb r0,[r0]
  mov r3,r0
  mov r4,r0
  @@ret:
  pop {r0-r1}
  sub r1,r6,r8
  b VWF_RETURN
  .pool

  .align
  REPLACE_PTR:
  .area 0x100,0
  .endarea
.endarea

; Jump to custom code from the text rendering function
.org 0x0203c860
  ; sub r1,r6,r8
  b VWF_FUNC
  VWF_RETURN:

; Remove line length limit
.org 0x0203ccc8
  mov r7,0xff

.org 0x0202e544
  ; .dw 0x022E8876
  .dw REPLACE_PTR
.org 0x02034130
  ; .dw 0x022E8876
  .dw REPLACE_PTR
.org 0x02039b14
  ; .dw 0x022E8876
  .dw REPLACE_PTR

; Redirect some error codes
ERROR_PTR equ 0x021c2394
.org 0x02055f30
  .dw ERROR_PTR
.org 0x02055f38
  .dw ERROR_PTR
.org 0x02055f40
  .dw ERROR_PTR
.org 0x0205615c
  .dw ERROR_PTR
.org 0x02056424
  .dw ERROR_PTR
.org 0x0205646c
  .dw ERROR_PTR
.org 0x020564cc
  .dw ERROR_PTR
.org 0x0205660c
  .dw ERROR_PTR
.org 0x02056610
  .dw ERROR_PTR
.org 0x02056618
  .dw ERROR_PTR
.org 0x0205668c
  .dw ERROR_PTR
.org 0x020566d4
  .dw ERROR_PTR
.org 0x02056908
  .dw ERROR_PTR
.org 0x0205698c
  .dw ERROR_PTR
.org 0x02056b40
  .dw ERROR_PTR
.org 0x02056b44
  .dw ERROR_PTR

.close
