INCLUDE "bugsite.inc"

SECTION "Window Manager Cursor Manipulation", ROM0[$0C24]
WindowManager_OpWINCOORD::
    call BugVM_PopTypedData
    ld a, c
    dec a
    ld [W_WindowManager_ContentsYMax], a
    
    call BugVM_PopTypedData
    ld a, c
    dec a
    ld [W_WindowManager_ContentsXMax], a
    
    call BugVM_PopTypedData
    ld a, c
    inc a
    ld [W_WindowManager_ContentsYMin], a
    
    call BugVM_PopTypedData
    ld a, c
    inc a
    ld [W_WindowManager_ContentsXMin], a
    
    call WindowManager_NewWindowFromCoordinates
    
    ld a, [W_WindowManager_ContentsXMin]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMin]
    ld [W_LCDC_PokeTileY], a
    
    ret
    
WindowManager_OpSCRCURS::
    ld a, (Banked_WindowManager_ADVICE_OpSCRCURS & $FF)
    call PatchSupport_PointCutByID
    ret
    
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    
WindowManager_OpWINCURS::
    ld a, (Banked_WindowManager_ADVICE_OpWINCURS & $FF)
    call PatchSupport_PointCutByID
    ret
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop