INCLUDE "bugsite.inc"

SECTION "BugVM Data Stack", WRAM0[$C200]
W_BugVM_DataStack:: ds $100

SECTION "BugVM Data Stack Counters", WRAM0[$C420]
W_BugVM_StackCounter:: ds 2

SECTION "BugVM Data Stack Utils", ROM0[$0611]
;Push a byte to the data stack.
;Will halt BugVM if the data stack overflows.
;This is not intended to be used by client code - the data stack is tagged and
;intended to contain 16-bit data, pointers, or bitfield indicies.
;ARGUMENTS:
; A = Data to push to stack.
BugVM_PushToDataStack::
    push af
    
    ldh a, [H_BugVM_DataFrame]
    
    ld l, a
    ld h, W_BugVM_DataStack >> 8
    
    pop af
    
    ld [hl], a
    ld hl, H_BugVM_DataFrame
    inc [hl]
    
    jr z, .die
    ret
    
.die
    jr .die

;Pop a byte from the data stack.
;Will halt BugVM if the data stack underflows.
;This is not intended to be used by client code - the data stack is tagged and
;intended to contain 16-bit data, pointers, or bitfield indicies.
;RETURNS:
; A = Data popped from stack.
BugVM_PopFromDataStack::
    ldh a, [H_BugVM_DataFrame]
    sub 1
    jr c, BugVM_PushToDataStack.die
    
    ld [H_BugVM_DataFrame], a
    
    ld l, a
    ld h, W_BugVM_DataStack >> 8
    
    ld a, [hl]
    ret
    
;Pop a BugVM word from the data stack.
;Will halt BugVM if the data stack underflows.
;Will always return an immediate value, even if the given data was originally
;an indirect or predicate pointer.
BugVM_PopTypedData::
    ld a, [W_BugVM_StackCounter]
    or a
    jr z, .readTag
    dec a
    ld [W_BugVM_StackCounter], a
    
.readTag
    call BugVM_PopFromDataStack
    cp M_BugVM_DataStackTagImmediate
    jr nz, .notImmediate
    
.readImmediate
    call BugVM_PopFromDataStack
    ld b, a
    call BugVM_PopFromDataStack
    ld c, a
    ret
    
.notImmediate
    cp M_BugVM_DataStackTagIndirect
    jr nz, .readPredicate
    
.readIndirect
    call BugVM_PopFromDataStack
    ld b, a
    call BugVM_PopFromDataStack
    ld l, a
    
    ld a, 3
    ld [REG_SVBK], a
    
    sla l
    rl b
    ld a, $C4
    add a, b
    ld h, a
    ld a, [hli]
    ld c, a
    ld b, [hl]
    ret
    
.readPredicate
    call BugVM_PopFromDataStack
    ld b, a
    call BugVM_PopFromDataStack
    ld c, a
    call BugVM_ReadPredicateArray
    ret