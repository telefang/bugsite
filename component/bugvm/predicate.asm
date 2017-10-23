INCLUDE "bugsite.inc"

SECTION "Bug VM Predicate Flags Array", WRAMX[$D800], BANK[$3]
W_BugVM_PredicateFlags:: ds $800 ;TODO: Is there actually this many flags?

SECTION "Bug VM Predicate Utilities", ROM0[$310D]
;Write to the predicate flags array.
;ARGUMENTS:
; DE = Bitfield index to write to
; 
BugVM_WritePredicateArray::
    push af
    
    ld a, BANK(W_BugVM_PredicateFlags)
    ld [REG_SVBK], a
    
    pop af ;why do we preserve A if we're just going to overwrite it?
    
    ld a, e
    and 7
    ld hl, W_BugVM_PredicateFlags
    srl d
    rr e
    srl d
    rr e
    srl d
    rr e
    add hl, de
    
    ld e, 1
    
.bitShiftLoop
    or a
    jr z, .checkBit
    rl e
    dec a
    jr .bitShiftLoop
    
.checkBit
    ld a, c
    or b
    jr z, .bitResetLoop
    
.bitSetLoop
    ld a, [hl]
    or e
    ld [hl], a
    jr .ret
    
.bitResetLoop
    ld a, e
    xor $FF
    ld e, a
    
    ld a, [hl]
    and e
    ld [hl], a
    
.ret
    ret
    
BugVM_ReadPredicateArray::
    push af
    
    ld a, BANK(W_BugVM_PredicateFlags)
    ld [REG_SVBK], a
    
    pop af
    
    ld a, c
    and 7
    ld hl, W_BugVM_PredicateFlags
    srl b
    rr c
    srl b
    rr c
    srl b
    rr c
    add hl, bc
    
    ld c, 1
    
.bitShiftLoop
    or a
    jr z, .extractBit
    rl c
    dec a
    jr .bitShiftLoop
    
.extractBit
    ld b, 0
    ld a, [hl]
    and c
    jr z, .bitZero
    
.bitOne
    ld c, 1
    jr .ret
    
.bitZero
    ld c, 0
    
.ret
    ret