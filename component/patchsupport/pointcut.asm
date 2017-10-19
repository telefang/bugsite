INCLUDE "bugsite.inc"

;There are precisely two locations in HOME which can accept patch code.
; HEADER: $0061-$00FF ($9F bytes)
; END:    $3DA0-$3DFF ($60 bytes)
;So instead we kick everything over to a patch table on bank 4, which has $1E00
;of empty space to go around.

SECTION "Patch Support Pointcut Call", ROM0[$0061]
;Execute patch advice by ID.
;The given ID in register A will be treated as an offset to the patch table.
;Current ROM bank will be preserved across the cut.
PatchSupport_PointCutByID::
    push hl
    ld l, a
    
    ld a, [H_System_CurrentROMBank]
    push af
    
    ld a, BANK(PatchSupport_PatchTable)
    rst $0
    
    ;Patch table must be aligned to 256-byte boundaries for this to work.
    ld h, PatchSupport_PatchTable >> 8
    call .advice
    
    pop af
    rst $0
    
    pop hl
    ret
    
.advice ;Z80 doesn't offer a call [hl] so let's improvise
    jp [hl]

PatchSupport_PointCutByID_END::