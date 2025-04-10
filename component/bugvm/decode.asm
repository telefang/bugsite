INCLUDE "bugsite.inc"

SECTION "BugVM Decode", ROM0[$05D1]
BugVM_ExecForever::
    call BugVM_LoadNextOpcode
    ld bc, BugVM_ExecForever
    push bc
    
BugVM_ExecOpcode::
    ld c, a
    ld b, 0
    sla c
    rl b
    ld a, b
    add a, (BugVM_OpcodeTable >> 8)
    ld b, a
    ld a, [bc]
    ld l, a
    inc bc
    ld a, [bc]
    ld h, a
    jp hl
    
BugVM_NOP::
    ret
    
BugVM_LoadNextOpcode::
    ldh a, [H_BugVM_PCBase]
    ld l, a
    ldh a, [H_BugVM_PCBase + 1]
    ld h, a
    
    ldh a, [H_BugVM_PCOffset]
    ld e, a
    ldh a, [H_BugVM_PCOffset + 1]
    ld d, a
    
    add hl, de
    inc de
    
    ld a, e
    ld [H_BugVM_PCOffset], a
    ld a, d
    ld [H_BugVM_PCOffset + 1], a
    
    ld a, h
    ld e, a
    and $3F
    add a, $40
    ld h, a
    
    ld a, e
    and $C0
    rlca
    rlca
    ld e, a
    
    ldh a, [H_BugVM_PCBank]
    add a, e
    rst 0
    ld a, [hl]
    ret