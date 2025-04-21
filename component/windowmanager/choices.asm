INCLUDE "bugsite.inc"

SECTION "Window Manager Choice String Storage", WRAMX[$D000], BANK[$1]
W_WindowManager_ChoiceStringStorage:: ds M_WindowManager_ChoiceStringStorageSize

SECTION "Window Manager Choice Counter", WRAM0[$C426]
W_WindowManager_ChoiceCounter:: ds 2

SECTION "Window Manager Poke Preserve", WRAM0[$C42C]
W_WindowManager_PokeXPreserve:: ds 2
W_WindowManager_PokeYPreserve:: ds 2

SECTION "Window Manager Choice Index", WRAM0[$C432]
W_WindowManager_BaseChoiceIndex:: ds 2

SECTION "Window Manager Choice Coords", WRAM0[$C43C]
W_WindowManager_ChoiceXCoord:: ds 2
W_WindowManager_ChoiceYCoord:: ds 2

SECTION "Window Manager Choice Managers", ROM0[$11FF]
WindowManager_PrintChoices::
    push af
    
    ld a, BANK(W_WindowManager_ChoiceStringStorage)
    ldh [REG_SVBK], a
    
    pop af
    ld a, [W_WindowManager_ContentsAttributes]
    push af
    
    or 8
    ld [W_WindowManager_ContentsAttributes], a
    
    ld a, [W_WindowManager_BaseChoiceIndex]
    swap a
    add a, 1
    ld c, a
    ld a, (W_WindowManager_ChoiceStringStorage >> 8)
    ld b, a
    
    ld a, [W_LCDC_PokeTileX]
    ld [W_WindowManager_ChoiceXCoord], a
    
    ld a, [W_LCDC_PokeTileY]
    ld [W_WindowManager_ChoiceYCoord], a
    
    ld a, [W_WindowManager_ChoiceCounter]
    ld e, a
    
.choicePrintLoop
    ld a, e
    or a
    jr z, .donePrintingChoices
    
    push bc
    push de
    
    ld a, [W_WindowManager_ChoiceXCoord]
    inc a
    ld [W_LCDC_PokeTileX], a
    
    ld a, [W_WindowManager_ChoiceYCoord]
    ld [W_LCDC_PokeTileY], a
    
    nop
    nop
    
    ld a, (Banked_WindowManager_ADVICE_PrintChoices & $FF)
    call PatchSupport_PointCutByID
    
    pop de
    pop bc
    dec e
    ld a, c
    add a, M_WindowManager_ChoiceStringSize
    ld c, a
    xor a
    adc a, b
    ld b, a
    jr .choicePrintLoop
    
.donePrintingChoices
    pop af
    ld [W_WindowManager_ContentsAttributes], a
    ret
    
WindowManager_CopyString::
    ld a, c
    or a
    jr z, .terminator
    
    ld a, [de]
    ld [hli], a
    
    inc de
    or a
    jr z, .terminator
    
    dec c
    jr WindowManager_CopyString
    
.terminator
    xor a
    ld [hl], a
    ret

SECTION "Window Manager Choice Opcodes", ROM0[$13B4]
WindowManager_OpWINCHOICE::
    ld a, [W_LCDC_PokeTileX]
    ld b, a
    ld a, [W_LCDC_PokeTileY]
    ld c, a
    push bc
    
    ld a, [W_WindowManager_ContentsAttributes]
    push af
    
    or 4
    ld [W_WindowManager_ContentsAttributes], a
    push af
    
    ld a, BANK(W_WindowManager_ChoiceStringStorage)
    ldh [REG_SVBK], a
    
    pop af
    ld a, [W_LCDC_PokeTileX]
    ld [W_LCDC_PokeTileX], a
    ld [W_WindowManager_PokeXPreserve], a
    
    ld a, [W_LCDC_PokeTileY]
    ld [W_WindowManager_PokeYPreserve], a
    
    xor a
    ld [W_WindowManager_ChoiceCounter], a
    
    ld a, [W_BugVM_StackCounter]
    ld c, a
    
.copyOptionStringsLoop
    ld a, c
    or a
    jr z, .optionsCopied
    
    dec c
    push bc
    call BugVM_PopTypedData
    
    ld d, b
    ld e, c
    ld a, [W_BugVM_StackCounter]
    swap a
    add a, 0
    ld l, a
    ld a, 0
    adc a, (W_WindowManager_ChoiceStringStorage >> 8)
    ld h, a
    ld a, $20
    ld [hli], a
    
    ld c, M_WindowManager_ChoiceStringSize
    call WindowManager_CopyString
    
    ld a, [W_WindowManager_ChoiceCounter]
    inc a
    ld [W_WindowManager_ChoiceCounter], a
    
    pop bc
    jr .copyOptionStringsLoop
    
.optionsCopied
    call WindowManager_PrintChoices
    
    pop af
    ld [W_WindowManager_ContentsAttributes], a
    
    pop bc
    ld a, c
    ld [W_LCDC_PokeTileY], a
    
    ld a, b
    ld [W_LCDC_PokeTileX], a
    ret