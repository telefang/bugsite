INCLUDE "bugsite.inc"

SECTION "Window Manager Contents Configuration Memory", WRAM0[$C4CE]
W_WindowManager_ContentsXMin:: ds 2
W_WindowManager_ContentsYMin:: ds 2
W_WindowManager_ContentsXMax:: ds 2
W_WindowManager_ContentsYMax:: ds 2
W_WindowManager_ContentsWidth:: ds 2
W_WindowManager_ContentsHeight:: ds 2
W_WindowManager_ContentsTmapAddr:: ds 2

SECTION "Window Manager Contents Config", ROM0[$0FAF]
;Given a properly configured X/Y-Min/Max set, configure the other bits of window
;config dependent on those coordinates.
WindowManager_NewWindowFromCoordinates::
    ld a, [W_WindowManager_ContentsXMin]
    ld c, a
    
    ld a, [W_WindowManager_ContentsXMax]
    sub c
    inc a
    ld [W_WindowManager_ContentsWidth], a
    
    ld a, [W_WindowManager_ContentsYMin]
    ld c, a
    
    ld a, [W_WindowManager_ContentsYMax]
    sub c
    inc a
    ld [W_WindowManager_ContentsHeight], a
    
    ld a, [W_WindowManager_ContentsXMin]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMin]
    ld [W_LCDC_PokeTileY], a
    
    push bc
    
    ld hl, H_LCDC_ShadowSCX
    ld a, [hli]
    ld c, a
    ld a, [hl]
    srl a
    rr c
    srl a
    rr c
    srl a
    rr c
    
    ld hl, H_LCDC_ShadowSCY
    ld a, [hli]
    ld b, a
    ld a, [hl]
    srl a
    rr b
    srl a
    rr b
    srl a
    rr b
    
    ld a, [W_LCDC_PokeTileX]
    ld l, a
    ld a, c
    add a, l
    and $1F
    ld l, a
    
    ld a, [W_LCDC_PokeTileY]
    ld h, a
    ld a, b
    add a, h
    and $1F
    ld h, a
    
    swap a
    rlca
    and $E0
    
    or l
    ld l, a
    srl h
    srl h
    srl h
    ld a, $98
    add a, h
    ld h, a
    
    pop bc
    
    ld a, l
    ld [W_WindowManager_ContentsTmapAddr], a
    ld a, h
    ld [W_WindowManager_ContentsTmapAddr + 1], a
    
    ret