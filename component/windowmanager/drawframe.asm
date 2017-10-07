INCLUDE "bugsite.inc"

SECTION "Window Manager Draw Utilities", ROM0[$1025]
;Draw a window frame.
;Relies on a validly configured window, as well as the appropriate tiles in VRAM
WindowManager_DrawFrame::
    ld a, [W_WindowManager_ContentsXMax]    ;Top-Right
	 inc a
	 ld [W_LCDC_PokeTileX], a
	 
	 ld a, [W_WindowManager_ContentsYMin]
	 dec a
	 ld [W_LCDC_PokeTileY], a
	 
	 ld a, $19
	 ld [H_LCDC_SetTileVal], a
	 call LCDC_PokeTilemap
	 
    ld a, [W_WindowManager_ContentsXMin]    ;Bottom-Left
	 dec a
	 ld [W_LCDC_PokeTileX], a
	 
	 ld a, [W_WindowManager_ContentsYMax]
	 inc a
	 ld [W_LCDC_PokeTileY], a
	 
	 ld a, $1A
	 ld [H_LCDC_SetTileVal], a
	 call LCDC_PokeTilemap
	 
    ld a, [W_WindowManager_ContentsXMax]    ;Bottom-Right
	 inc a
	 ld [W_LCDC_PokeTileX], a
	 
	 ld a, [W_WindowManager_ContentsYMax]
	 inc a
	 ld [W_LCDC_PokeTileY], a
	 
	 ld a, $1B
	 ld [H_LCDC_SetTileVal], a
	 call LCDC_PokeTilemap
	 
    ld a, [W_WindowManager_ContentsXMin]    ;Top-Left
	 dec a
	 ld [W_LCDC_PokeTileX], a
	 
	 ld a, [W_WindowManager_ContentsYMin]
	 dec a
	 ld [W_LCDC_PokeTileY], a
	 
	 ld a, $18
	 ld [H_LCDC_SetTileVal], a
	 call LCDC_PokeTilemap
    
    ld a, [W_WindowManager_ContentsXMin]    ;Left/right borders
    ld [W_LCDC_PokeTileX], a
    
    ld a, [W_WindowManager_ContentsWidth]
    ld c, a
    
.vertFrameLoop
    ld a, c
    or a
    jr z, .prepHorizLoop
    
    ld a, $1C
    ld [H_LCDC_SetTileVal], a
    
    ld a, [W_WindowManager_ContentsYMin]    ;Left border
    dec a
    ld [W_LCDC_PokeTileY], a
    call LCDC_PokeTilemap
    
    ld a, $1D
    ld [H_LCDC_SetTileVal], a
    
    ld a, [W_WindowManager_ContentsYMax]    ;Right border
    inc a
    ld [W_LCDC_PokeTileY], a
    call LCDC_PokeTilemap
    
    ld a, [W_LCDC_PokeTileX]
    inc a
    ld [W_LCDC_PokeTileX], a
    
    dec c
    jr .vertFrameLoop
    
.prepHorizLoop
    ld a, [W_WindowManager_ContentsYMin]    ;Top/bottom borders
    ld [W_LCDC_PokeTileY], a
    
    ld a, [W_WindowManager_ContentsHeight]
    ld c, a
    
.horizFrameLoop
    ld a, c
    or a
    jr z, .fillFrameCenter
    
    ld a, $1E
    ld [H_LCDC_SetTileVal], a
    
    ld a, [W_WindowManager_ContentsXMin]    ;Top border
    dec a
    ld [W_LCDC_PokeTileX], a
    call LCDC_PokeTilemap
    
    ld a, $1F
    ld [H_LCDC_SetTileVal], a
    
    ld a, [W_WindowManager_ContentsXMax]    ;Bottom border
    inc a
    ld [W_LCDC_PokeTileX], a
    call LCDC_PokeTilemap
    
    ld a, [W_LCDC_PokeTileY]
    inc a
    ld [W_LCDC_PokeTileY], a
    
    dec c
    jr .horizFrameLoop
    
.fillFrameCenter
    call WindowManager_ClearRegion  ;Frame center
    
    ld a, [W_WindowManager_MenuItemSelected]
    cp $FF
    jr z, .windowNotScrollable
    
.windowIsScrollable
    call WindowManager_DrawOverflowArrows
    
.windowNotScrollable
    ld a, [W_WindowManager_ContentsXMin]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMin]
    ld [W_LCDC_PokeTileY], a
    
    ret
    
;Draw/update the overflow arrows on windows with menu items in them.
WindowManager_DrawOverflowArrows::
    ld a, [W_WindowManager_ContentsXMax]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMin]
    ld [W_LCDC_PokeTileY], a
    
    ld a, [W_WindowManager_MenuItemSelected]
    or a
    jr z, .selectUpSpace
    
.selectUpArrow
    ld a, 9
    jr .drawUpTile
    
.selectUpSpace
    ld a, $20
    
.drawUpTile
    ld [H_LCDC_SetTileVal], a
    call LCDC_PokeTilemap
    
    ld a, [W_WindowManager_ContentsXMax]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsYMax]
    ld [W_LCDC_PokeTileY], a
    
    ld a, [W_WindowManager_MenuItemCount]
    ld c, a
    ld a, [W_WindowManager_MenuItemSelected]
    cp c
    jr nc, .selectDownSpace
    
.selectDownArrow
    ld a, $A
    jr .drawDownTile
    
.selectDownSpace
    ld a, $20
    
.drawDownTile
    ld [H_LCDC_SetTileVal], a
    call LCDC_PokeTilemap
    
    ret
    
;Set all tiles within the Contents region to spaces.
WindowManager_ClearRegion::
    ld a, [W_LCDC_PokeTileX]
    ld b, a
    ld a, [W_LCDC_PokeTileY]
    ld c, a
    
    push bc
    
    ld a, [W_WindowManager_ContentsYMin]
    ld [W_LCDC_PokeTileY], a
    ld a, [W_WindowManager_ContentsHeight]
    ld c, a
    
    ld a, $20
    ld [H_LCDC_SetTileVal], a
    
.rowClearLoop
    ld a, c
    or a
    jr z, .doneClearing
    
    push bc
    ld a, [W_WindowManager_ContentsXMin]
    ld [W_LCDC_PokeTileX], a
    ld a, [W_WindowManager_ContentsWidth]
    ld c, a
    
.tileClearLoop
    ld a, c
    or a
    jr z, .nextRow
    
    call LCDC_PokeTilemap
    
    ld a, [W_LCDC_PokeTileX]
    inc a
    ld [W_LCDC_PokeTileX], a
    
    dec c
    
    jr .tileClearLoop
    
.nextRow
    ld a, [W_LCDC_PokeTileY]
    inc a
    ld [W_LCDC_PokeTileY], a
    
    pop bc
    dec c
    
    jr .rowClearLoop

.doneClearing
    pop bc
    
    ld a, c
    ld [W_LCDC_PokeTileY], a
    ld a, b
    ld [W_LCDC_PokeTileX], a
    
    ret