.nds

.open "VampireData/repack/arm9.bin",0x02000000


.org 0x21c282c
.area 0x443,0  ; up to 0x021c2c6f
  FONT_DATA:
  .import "VampireData/font_data.bin"
  .align
  DICTIONARY_DATA:
  .include "VampireData/dictionary.asm"
  .align
.endarea


.org 0x21c23c8
.area 0x433,0  ; up to 0x021c27fb
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


  DICTIONARY_DAT:
  cmp r1,0x1
  bne @@ret
  ; Get the output string pointer
  ; Do this before pushing registers on the stack
  add r1,sp,0x14
  push {r0,r2}
  ; Get the current offset in the output string
  mov r2,r12
  ; Get the dictionary entry and increase input pointer
  ldrb r0,[r5]
  add r5,r5,0x1
  ; Call the dictionary function
  bl DICTIONARY_FUNC
  ; Store the new offset
  mov r12,r0
  ; Return to normal execution
  pop {r0,r2}
  mov r1,0x1
  b DICTIONARY_DAT_NORMAL
  @@ret:
  cmp r1,0x9
  b DICTIONARY_DAT_RETURN


  DICTIONARY:
  @@read_text_byte equ 0x0202cd50
  ; Check if r0 is <= 0xa
  cmp r0,0xa
  ble DICTIONARY_RETURN
  ; Get the output string pointer
  add r1,sp,0x40
  ; Get the current offset in the output string
  ; Do this before pushing registers on the stack
  ldrsh r2,[sp,0x28]
  ; Check if we're dealing with a compressed string, bit 7 is set
  cmp r0,0x80
  bge @@compression
  ; Call the dictionary function
  bl DICTIONARY_FUNC
  b @@ret

  @@compression:
  @@addregs equ 4*4
  push {r3-r6}
  ; Drop the check bit, this is the length we need to copy
  and r4,r0,0x7f
  ; Read 2 bytes
  add r0,sp,0x3c+@@addregs
  add r1,sp,0x38+@@addregs
  bl @@read_text_byte
  mov r5,r0
  add r0,sp,0x3c+@@addregs
  add r1,sp,0x38+@@addregs
  bl @@read_text_byte
  lsl r6,r0,0x8
  orr r5,r6,r5
  ; Setup other registers
  add r1,sp,0x40+@@addregs
  ldrsh r2,[sp,0x28+@@addregs]
  ; Set r5 to the actual offset
  add r6,sp,0x3c+@@addregs
  ldr r6,[r6]
  sub r5,r6,r5
  ; r1 = output string pointer
  ; r2 = current offset in the output string
  ; r4 = length to copy
  ; r5 = input pointer
  @@loop:
  cmp r4,0x0
  ble @@end
  ; Read one byte
  sub r4,r4,0x1
  ldrb r0,[r5]
  add r5,r5,0x1
  ; Check if it's a dictionary entry
  cmp r0,0x1
  beq @@dict
  ; Store it in the output string
  strb r0,[r1,r2]
  add r9,r9,0x1
  add r2,r2,0x1
  b @@loop
  @@dict:
  ; Read dictionary entry
  ldrb r0,[r5]
  add r5,r5,0x1
  sub r4,r4,0x1
  bl DICTIONARY_FUNC
  mov r2,r0
  mov r9,r0
  b @@loop
  @@end:
  mov r0,r2
  pop {r3-r6}

  @@ret:
  ; Store the new offset
  strh r0,[sp,0x28]
  ; Return to normal execution
  mov r0,0xb
  cmp r0,0xa
  b DICTIONARY_NORMAL


  ; r0 = dictionary entry
  ; r1 = output string pointer
  ; r2 = output offset
  DICTIONARY_FUNC:
  push {lr,r3-r4}
  ; Get the dictionary pointer
  sub r0,r0,0xb
  lsl r0,r0,0x2
  ldr r3,=DICTIONARY_DATA
  add r0,r0,r3
  ldr r0,[r0]
  ; Copy the dictionary data to the output string
  mov r3,0x0
  @@loop:
  ldrb r4,[r0,r3]
  cmp r4,0x0
  moveq r0,r2
  beq @@ret
  strb r4,[r1,r2]
  add r2,r2,0x1
  add r3,r3,0x1
  b @@loop
  @@ret:
  pop {pc,r3-r4}
  .pool
.endarea

; Edit the function that copies the hardcoded name to handle variable length names
; Always add a space
.org 0x0202c8e0
  ; cmp r2,0x6
  cmp r2,0xff
; Put a normal space instead of a wide one
.org 0x0202c924
  mov r1,0x90
  strb r1,[r0,r12]
  mov r1,0x10
; Get the correct byte for the 2nd part of the name
;.org 0x0202c940
  ; ldrsb r1,[r1,0x7]
  ;ldrsb r1,[r1,0x10]

.org 0x021c3018
.area 0x1bf,0  ; up to 0x021c31d7
  .align
  REPLACE_PTR:
  .area 0x100,0
  .endarea
  NAME_PTR1:
  .area 0x10,0
  .endarea
  NAME_PTR2:
  .area 0x10,0
  .endarea
.endarea

; Don't execute this code after loading the names, it's not needed and limits them to a length of 7
.org 0x0203b4f8
  pop {r3-r5,pc}

; Jump to custom code from the text rendering function
.org 0x0203c860
  ; sub r1,r6,r8
  b VWF_FUNC
  VWF_RETURN:

; Remove line length limit
.org 0x0203ccc8
  mov r7,0xff

; Jump to custom code from the text parsing function
.org 0x0202d9e4
  ; cmp r0,0xa
  b DICTIONARY
  DICTIONARY_RETURN:
.org 0x0202ddb0
  DICTIONARY_NORMAL:

; Jump to custom code from the DAT text parsing function
.org 0x0203ce6c
  ; cmp r1,0x9
  b DICTIONARY_DAT
  DICTIONARY_DAT_RETURN:
.org 0x0203cf04
  DICTIONARY_DAT_NORMAL:


; Replace strlen calls with our custom one
; 0x0203c9b8
.org 0x0202c994
  bl STRLEN_DIV
.org 0x02047ea4
  bl STRLEN_DIV
; 0x0203d190
.org 0x0203d3e0
  bl STRLEN_DIV
.org 0x0204c7d0
  bl STRLEN_DIV
.org 0x0204c828
  bl STRLEN_DIV
.org 0x0204c880
  bl STRLEN_DIV
.org 0x0204c8d8
  bl STRLEN_DIV
.org 0x0204c930
  bl STRLEN_DIV
.org 0x0204c988
  bl STRLEN_DIV
.org 0x0204c9d8
  bl STRLEN_DIV


; Tweak character name positioning
; Normally, this function returns an hardcoded value for every possible string length
.org 0x202c980  ; Until 0x0202ca38
  .area 0xb8
  push {lr,r1,r4}
  mov r4,r1
  cmp r0,0x0
  cmpne r4,0x0
  popeq {pc,r1,r4}
  bl STRLEN
  mov r1,r0
  lsr r1,r1,0x12
  lsl r1,r1,0x1
  add r0,r0,0x2b
  sub r0,r0,r1
  str r0,[r4]
  pop {pc,r1,r4}

  STRLEN_DIV:
  push {lr,r1}
  bl STRLEN
  ; Divide by 6: ((x * 0xaaab) >> 0x10) >> 0x2
  ldr r1,=0xaaab
  mul r0,r0,r1
  lsr r0,r0,0x10
  lsr r0,r0,0x2
  pop {pc,r1}
  .pool

  STRLEN:
  push {lr,r1-r4}
  ldr r1,=FONT_DATA
  mov r3,0x90
  mov r4,0x0
  ; Add the font width in r4
  @@loop:
  ldrb r2,[r0],0x1
  cmp r2,0x0
  beq @@end
  ; Check if this is a group
  cmp r2,0x90
  movge r3,r2
  bge @@loop
  ; If this isn't group 0x90, just add a fixed value
  cmp r3,0x91
  addeq r4,r4,6
  beq @@loop
  addgt r4,r4,12
  bgt @@loop
  ; Get the character width
  add r2,r1,r2
  sub r2,r2,0x10
  ldrb r2,[r2]
  add r4,r4,r2
  b @@loop
  @@end:
  ; Return
  mov r0,r4
  pop {pc,r1-r4}
  .pool
  .endarea


; Redirect processed strings pointer to a larger space
.org 0x0202e544
  ; .dw 0x022E8876
  .dw REPLACE_PTR
.org 0x02034130
  ; .dw 0x022E8876
  .dw REPLACE_PTR
.org 0x02039b14
  ; .dw 0x022E8876
  .dw REPLACE_PTR

/*
; Redirect name pointers to a larger space
.org 0x0202c970
  .dw NAME_PTR1
.org 0x0202e528
  .dw NAME_PTR1
.org 0x0203b67c
  .dw NAME_PTR1
.org 0x0203bedc ;?
  .dw NAME_PTR1
.org 0x0203c1e8 ;?
  .dw NAME_PTR1
.org 0x020433d0 ;?
  .dw NAME_PTR1
.org 0x020440b4 ;also change the ldrsb 0x7?
  .dw NAME_PTR1
.org 0x0204477c
  .dw NAME_PTR1

.org 0x0202c974
  .dw NAME_PTR2
.org 0x0202e524
  .dw NAME_PTR2
.org 0x0203b680
  .dw NAME_PTR2
.org 0x020433d4
  .dw NAME_PTR2
.org 0x0204478c
  .dw NAME_PTR2
*/

; Redirect some error codes
ERROR_PTR equ 0x021c2394
UNKNOWN_PTR equ 0x021c3010
.org 0x02057ec4
  .dw ERROR_PTR
.org 0x02058118
  .dw ERROR_PTR
.org 0x0205811c
  .dw ERROR_PTR
.org 0x02058120
  .dw ERROR_PTR
.org 0x02058124
  .dw ERROR_PTR
.org 0x02058190
  .dw ERROR_PTR
.org 0x02058194
  .dw ERROR_PTR
.org 0x02058198
  .dw ERROR_PTR
.org 0x0205819c
  .dw ERROR_PTR
.org 0x0205820c
  .dw ERROR_PTR
.org 0x02058210
  .dw ERROR_PTR
.org 0x02058214
  .dw ERROR_PTR
.org 0x02058218
  .dw ERROR_PTR
.org 0x0205829c
  .dw ERROR_PTR
.org 0x020582a0
  .dw ERROR_PTR
.org 0x020582a4
  .dw ERROR_PTR
.org 0x020582a8
  .dw ERROR_PTR
.org 0x02058350
  .dw ERROR_PTR
.org 0x02058354
  .dw ERROR_PTR
.org 0x02058358
  .dw ERROR_PTR
.org 0x0205835c
  .dw ERROR_PTR
.org 0x02058514
  .dw ERROR_PTR
.org 0x02058518
  .dw ERROR_PTR
.org 0x0205851c
  .dw ERROR_PTR
.org 0x02058520
  .dw ERROR_PTR
.org 0x02058524
  .dw ERROR_PTR
.org 0x02058528
  .dw ERROR_PTR
.org 0x020586a8
  .dw ERROR_PTR
.org 0x020586ac
  .dw ERROR_PTR
.org 0x020586b0
  .dw ERROR_PTR
.org 0x020586b4
  .dw ERROR_PTR
.org 0x02058874
  .dw ERROR_PTR
.org 0x02058878
  .dw ERROR_PTR
.org 0x0205887c
  .dw ERROR_PTR
.org 0x02058880
  .dw ERROR_PTR
.org 0x02058884
  .dw ERROR_PTR
.org 0x02058888
  .dw ERROR_PTR
.org 0x020589a8
  .dw ERROR_PTR
.org 0x020589ac
  .dw ERROR_PTR
.org 0x020589b0
  .dw ERROR_PTR
.org 0x020589b4
  .dw ERROR_PTR
.org 0x02058a20
  .dw ERROR_PTR
.org 0x02058a24
  .dw ERROR_PTR
.org 0x02058a28
  .dw ERROR_PTR
.org 0x02058a2c
  .dw ERROR_PTR
.org 0x02058a98
  .dw ERROR_PTR
.org 0x02058a9c
  .dw ERROR_PTR
.org 0x02058aa0
  .dw ERROR_PTR
.org 0x02058aa4
  .dw ERROR_PTR
.org 0x02058b10
  .dw ERROR_PTR
.org 0x02058b14
  .dw ERROR_PTR
.org 0x02058b18
  .dw ERROR_PTR
.org 0x02058b1c
  .dw ERROR_PTR

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
.org 0x02056bec
  .dw ERROR_PTR
.org 0x02056cd4
  .dw ERROR_PTR
.org 0x02056cd8
  .dw ERROR_PTR
.org 0x02056de8
  .dw ERROR_PTR
.org 0x02056dec
  .dw ERROR_PTR
.org 0x02056f14
  .dw ERROR_PTR
.org 0x02056fd4
  .dw ERROR_PTR
.org 0x0205776c
  .dw ERROR_PTR
.org 0x02057b40
  .dw ERROR_PTR

.org 0x020597b8
  .dw ERROR_PTR
.org 0x02059858
  .dw ERROR_PTR
.org 0x0205985c
  .dw ERROR_PTR
.org 0x02059938
  .dw ERROR_PTR
.org 0x0205993c
  .dw ERROR_PTR
.org 0x02059944
  .dw ERROR_PTR
.org 0x02059948
  .dw UNKNOWN_PTR
.org 0x02059c80
  .dw ERROR_PTR
.org 0x02059c84
  .dw ERROR_PTR
.org 0x02059c88
  .dw ERROR_PTR
.org 0x02059e28
  .dw ERROR_PTR
.org 0x02059e30
  .dw ERROR_PTR

.close
