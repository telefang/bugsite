INCLUDE "bugsite.inc"

SECTION "Window Manager Print Tools Memory", WRAM0[$C45E]
W_WindowManager_LastSampledInput:: ds 2

SECTION "Window Manager Print Tools", ROM0[$0CEE]
;Called to draw text. Draws all text until null terminator.
;ARGUMENTS:
; BC = Memory to draw text from.
WindowManager_PrintText::
    ld a, [bc]
    or a
    ret z
    
    ld [H_LCDC_SetTileVal], a
    inc bc
    call WindowManager_AutoNewline
    
    ld a, [H_LCDC_SetTileVal]
    cp $5C
    jr z, .newline
    cp $7F
    jr z, .playerNameOp
    
.normalCharacter
    ld a, Banked_WindowManager_ADVICE_PrintChara & $FF
    call PatchSupport_PointCutByID
    
    ld a, [W_WindowManager_ContentsAttributes]
    bit 2, a
    jr nz, WindowManager_PrintText
    
    ld a, [H_Input_JoypadState]
    and 1
    ld a, 1
    jr nz, .noButtonPressed
    
.buttonPressed
    ld a, [W_WindowManager_ContentsTextSpeed]
    
.noButtonPressed
    push bc
    ld c, a
    call SpriteManager_AnimateSpritesForFrameCount
    
    pop bc
    jr WindowManager_PrintText
    
.newline
    ld a, Banked_WindowManager_ADVICE_PrintNewline & $FF
    call PatchSupport_PointCutByID
    
    call WindowManager_NewlineMoveback
    jr WindowManager_PrintText
    
.playerNameOp
    push bc
    call MainScript_PrintPlayerName
    pop bc
    jr WindowManager_PrintText
    
;Opcodes to print out text after calling certain functions which are now NOPs.
;I assume these were for debugging purposes at some point in the game.
.debug1
    push bc
    call $1659  ;NOP
    pop bc
    jr WindowManager_PrintText
    
.debug2
    push bc
    call $1629  ;NOP
    pop bc
    jr WindowManager_PrintText
    
WindowManager_AutoNewline::
    ld e, a
    ld a, [W_WindowManager_ContentsAttributes]
    bit 3, a
    jr nz, .ret
    
    ld a, [W_WindowManager_ContentsXMax]
    ld d, a
    
    ld a, [W_LCDC_PokeTileX]
    cp d
    jr c, .ret
    
    jr nz, .applyAutoNewline
    
    ld a, e
    cp $DE
    jr z, .ret
    cp $DF
    jr z, .ret
    cp $A3
    jr z, .ret
    cp $A1
    jr z, .ret
    cp $A4
    jr z, .ret
    cp $21
    jr z, .ret
    cp $3F
    jr z, .ret
    cp $00
    jr z, .ret
    
.applyAutoNewline
    ld a, [W_WindowManager_ContentsXMin]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMax]
    ld d, a
    
    ld a, [W_LCDC_PokeTileY]
    inc a
    cp d
    jr c, .noScrollupContents
    
.scrollupContents
    push bc
    
    call WindowManager_ScrollUpContents
    call WindowManager_ScrollUpContents
    
    pop bc
    jr .ret
    
.noScrollupContents
    ld a, [W_LCDC_PokeTileY]
    inc a
    inc a
    ld [W_LCDC_PokeTileY], a
    
.ret
    ret
    
WindowManager_NewlineMoveback::
    ld a, [W_WindowManager_ContentsXMin]
    ld e, a
    
    ld a, [W_LCDC_PokeTileX]
    cp e
    jr z, .noMoveback
    
    ld a, [W_WindowManager_ContentsXMax]
    inc a
    ld [W_LCDC_PokeTileX], a
    
.noMoveback
    ret
    
WindowManager_WaitForInput::
    ld a, [W_LCDC_SetAttrVal]
    
    push af
    
    and $F8
    or 7
    ld [W_LCDC_SetAttrVal], a
    
    ld a, [W_LCDC_PokeTileX]
    ld b, a
    ld a, [W_LCDC_PokeTileY]
    ld c, a
    
    push bc
    
    xor a
    ld b, a
    
.spinLoop
    ld a, [H_Input_JoypadChanged]
    ld [W_WindowManager_LastSampledInput], a
    
    and 3
    jr nz, .inputRecieved
    
    ld a, [W_WindowManager_ContentsXMax]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMax]
    ld [W_LCDC_PokeTileY], a
    
    ld a, b
    and $10
    jr z, .blinkState
    
    ld a, $FE
    jr .selectTileAndDraw
    
.blinkState
    ld a, $20
    
.selectTileAndDraw
    ld [H_LCDC_SetTileVal], a
    call LCDC_PokeTilemap
    
    push bc
    
    call SpriteManager_AnimateSprites
    
    pop bc
    
    inc b
    jr .spinLoop
    
.inputRecieved
    ld a, [W_WindowManager_ContentsXMax]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMax]
    ld [W_LCDC_PokeTileY], a
    ld a, $20
    ld [H_LCDC_SetTileVal], a
    call LCDC_PokeTilemap
    
    pop bc
    
    ld a, b
    ld [W_LCDC_PokeTileX], a
    ld a, c
    ld [W_LCDC_PokeTileY], a
    
    pop af
    
    ld [W_LCDC_SetAttrVal], a
    ret