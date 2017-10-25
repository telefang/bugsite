INCLUDE "bugsite.inc"

SECTION "Window Manager - Op WINCLR", ROM0[$97C]
WindowManager_OpWINCLR::
    call WindowManager_ClearRegion
    
    ld a, [W_WindowManager_ContentsXMin]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMin]
    ld [W_LCDC_PokeTileY], a
    
    ret