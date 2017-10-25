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
    call BugVM_PopTypedData
    ld a, c
    ld [W_LCDC_PokeTileY], a
    
    call BugVM_PopTypedData
    ld a, c
    ld [W_LCDC_PokeTileX], a
    
    ret
    
WindowManager_OpWINCURS::
    call BugVM_PopTypedData
    ld a, [W_WindowManager_ContentsYMin]
    add a, c
    ld [W_LCDC_PokeTileY], a
    
    call BugVM_PopTypedData
    ld a, [W_WindowManager_ContentsXMin]
    add a, c
    ld [W_LCDC_PokeTileX], a
    
    ret