INCLUDE "bugsite.inc"

SECTION "Name Input String Temporary", WRAM0[$C8E0]
W_NameInput_NameTemporaryHolding:: ds M_NameInput_NameTemporaryHoldingSize

SECTION "Name Input String Temporary Opcodes", ROM0[$1670]
;Opcode $B1
NameInput_OpNTPRINT::
    ld bc, W_NameInput_NameTemporaryHolding
    call WindowManager_PrintText
    ret
    
;Opcode $B0
NameInput_OpNTSTR::
    call BugVM_PopTypedData
    ld hl, W_NameInput_NameTemporaryHolding
    ld e, M_NameInput_NameTemporaryHoldingSize - 1
    
.copyLoop
    ld a, [bc]
    or a
    jr z, .terminate
    
    ld [hli], a
    inc bc
    dec e
    jr z, .terminate
    jr .copyLoop
    
.terminate
    xor a
    ld [hl], a
    ret