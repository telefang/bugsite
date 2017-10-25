INCLUDE "bugsite.inc"

SECTION "WindowManager VWF Advice Memory", WRAMX[$DFC6], BANK[$2]
;VRAM for variable-width font tiles is stored into a ring buffer.
;Each print operation draws tiles into the buffer, overwriting previous tiles
;if ring space is exhausted. This is a good strategy for dialogue windows, but
;text heavy windows may instead want to switch between multiple rings for
;different purposes. All rings are specified as background tile indicies in
;VRAM bank zero.
W_WindowManager_VWFRingStart: ds 1 ;tiles from $8800
W_WindowManager_VWFRingEnd: ds 1
W_WindowManager_VWFRingWriteHead: ds 1
W_WindowManager_CompositionState: ds 1
W_WindowManager_CompositionShift: ds 1
W_WindowManager_CompositionFont: ds 2
W_WindowManager_CompositionBackground: ds 2
W_WindowManager_CompositionArea: ds $20 ;two tiles, identical to VRAM

SECTION "WindowManager VWF Advice", ROMX[$6200], BANK[$3]
;Flush composition area into the VWF ring.
WindowManager_ADVICE_FlushCompositionArea::
    push hl
    push de
    push bc
    push af
    
    ld a, [W_WindowManager_CompositionState]
    cp M_WindowManager_CompositionStateUninitialized
    jr z, .emptyTile
    
    ld de, $8800
    ld a, [W_WindowManager_VWFRingWriteHead]
    push af
    and $F0
    swap a
    add d
    ld d, a
    pop af
    and $0F
    swap a
    add e
    ld e, a
    
    ;Check if either of the two compo tiles are dirty.
.dirtyLoop
    ld a, [W_WindowManager_CompositionState]
    bit 3, a
    jr nz, .inverseCheckOrder
    
.properCheckOrder
    bit 1, a
    jr nz, .selectFirstCompoTile
    bit 2, a
    jr nz, .selectSecondCompoTile
    jr .emptyTile
    
    ;We invert the check order if TileOrderReverse is set so that the drawing
    ;function can treat the composition area as a 2-tile ring buffer. Dirty
    ;bits tell us what to copy and reverse bits tell us in what order.
.inverseCheckOrder
    bit 2, a
    jr nz, .selectSecondCompoTile
    bit 1, a
    jr nz, .selectFirstCompoTile
    jr .emptyTile
    
.selectFirstCompoTile
    ld hl, W_WindowManager_CompositionArea
    res 1, a
    jr .doVmemcpy
    
.selectSecondCompoTile
    ld hl, W_WindowManager_CompositionArea + $10
    res 2, a
    
.doVmemcpy
    ld [W_WindowManager_CompositionState], a
    
    ld a, 0
    ld [REG_VBK], a
    
    ld bc, $10
    call LCDC_vmemcopy
    
    ;Move up the target pointer in case both tiles are dirty.
    ld a, [W_WindowManager_VWFRingWriteHead]
    ld d, a
    ld a, [W_WindowManager_VWFRingEnd]
    cp d
    jr z, .headOverflow
    
.noHeadOverflow
    inc d
    ld a, d
    jr .nextTilePtrCalc
    
.headOverflow
    ld a, [W_WindowManager_VWFRingStart]
    inc a

.nextTilePtrCalc
    ld de, $8800
    push af
    and $F0
    swap a
    add d
    ld d, a
    pop af
    and $0F
    swap a
    add e
    ld e, a
    
    jr .dirtyLoop
    
.emptyTile
    pop af
    pop bc
    pop de
    pop hl
    ret
    
;Increment the ring buffer and composition area by a certain number of pixels.
;Also clears previous composition area tiles for further use.
;Returns a = zero if tile was not incremented, nonzero if it was.
;NOTE: Do not call if there are dirty tiles in the composition area.
;They may be lost, flipped around, etc.
; ARGUMENTS: (A) The width of the last character drawn.
WindowManager_ADVICE_IncrementRingByPixels::
    push bc
    push de
    push hl
    
    ld l, a
    ld a, [W_WindowManager_CompositionShift]
    add l
    ld [W_WindowManager_CompositionShift], a
    
    ;Update the reverse bit.
    ld b, a
    ld a, [W_WindowManager_CompositionState]
    bit 3, b
    jr z, .shouldNotBeReverseMode
    
.shouldBeReverseMode
    ld b, a
    set 3, a
    bit 3, b
    jr z, .setStateAndIncrementRing ;If it wasn't set before, and now it is...
    jr .setState
    
.shouldNotBeReverseMode
    ld b, a
    res 3, a
    bit 3, b
    jr nz, .setStateAndIncrementRing ;If it was set before, and now it isn't...
    
.setState
    ld [W_WindowManager_CompositionState], a
    jr .noStateChangeNeeded
    
.setStateAndIncrementRing
    ld [W_WindowManager_CompositionState], a
    
    ;Clear the previous "first" composition area, which is now the second one,
    ;so that composing onto it doesn't bring garbage in
    ld a, [W_WindowManager_CompositionState]
    bit 3, a
    jr nz, .eraseFirstTile
    
.eraseSecondTile
    ld hl, W_WindowManager_CompositionArea + $10
    jr .eraseTileLoop
    
.eraseFirstTile
    ld hl, W_WindowManager_CompositionArea
    
.eraseTileLoop
    ld a, [W_WindowManager_CompositionBackground]
    ld d, a
    ld a, [W_WindowManager_CompositionBackground + 1]
    ld e, a
    
    REPT $8
    ld a, d
    ld [hli], a
    ld a, e
    ld [hli], a
    ENDR
    
    ;If we flipped the reverse bit, we crossed a tile boundary, so we need to
    ;move onto the next tile in the ring.
    ld a, [W_WindowManager_VWFRingWriteHead]
    ld l, a
    ld a, [W_WindowManager_VWFRingEnd]
    cp l
    
    jr z, .headOverflow
    
.noHeadOverflow
    inc l
    ld a, l
    jr .setRingHead
    
.headOverflow
    ld a, [W_WindowManager_VWFRingStart]

.setRingHead
    ld [W_WindowManager_VWFRingWriteHead], a
    
    ld a, 1
    jr .ret
    
.noStateChangeNeeded
    ld a, 0
    
.ret
    pop hl
    pop de
    pop bc
    ret
    
;Draw a letter into the current composition area.
;Argument A: Character being drawn.
WindowManager_ADVICE_ComposeCharacter::
    push hl
    push de
    push bc
    push af
    ld a, [W_WindowManager_CompositionFont]
    ld c, a
    ld a, [W_WindowManager_CompositionFont + 1]
    ld b, a
    
    pop af
    add $80 ;tiles are stored 'backwards', for the sake of tile text mode
    ld d, 0
    ld e, a
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    
    call PatchSupport_ReadBugFSFile
    
    ld hl, W_PatchUtils_FileBuffer
    
    ld a, [W_WindowManager_CompositionShift]
    and $07
    ld b, a
    
    ld a, $ff
    bit 0, b
    jr z, .secondBitMask
    srl a
    
.secondBitMask
    bit 1, b
    jr z, .thirdBitMask
    srl a
    srl a
    
.thirdBitMask
    bit 2, b
    jr z, .charaMaskMade
    srl a
    srl a
    srl a
    srl a
    
.charaMaskMade
    cpl
    ld c, a
    push bc ;shift count and bitmask
    
    ;Check which composition area to start from.
    ld a, [W_WindowManager_CompositionState]
    bit 3, a
    jr nz, .reverseFirstTile
    
.noReverseFirstTile
    ld de, W_WindowManager_CompositionArea
    jr .startCompositionFirst
    
.reverseFirstTile
    ld de, W_WindowManager_CompositionArea + $10
    
.startCompositionFirst
    ld hl, W_PatchUtils_FileBuffer
    ld a, 16
    
.compoLoopFirst
    push af
    push bc ;b = shift count, c = mask
    
    ;Mask off the existing composition data.
    ld a, [de]
    and c
    ld c, a
    
    ;Shift in the new composition data.
    ld a, [hli]
    
    bit 0, b
    jr z, .secondBitFirst
    srl a
    
.secondBitFirst
    bit 1, b
    jr z, .thirdBitFirst
    srl a
    srl a
    
.thirdBitFirst
    bit 2, b
    jr z, .composeLineFirst
    srl a
    srl a
    srl a
    srl a
    
    ;Mix both characters and store the composed data.
.composeLineFirst
    or c
    ld [de], a
    inc de
    
    pop bc
    pop af
    dec a
    jr nz, .compoLoopFirst
    
    ;First tile's composed. Move onto the second tile, if necessary, and then
    ;set the dirty bit.
    ld a, [W_WindowManager_CompositionState]
    bit 3, a
    jr nz, .reverseSecondTile
    
.noReverseSecondTile
    set 1, a ;Dirty first tile
    
    ld de, W_WindowManager_CompositionArea + $10
    jr .startCompositionSecond

.reverseSecondTile
    set 2, a ;Dirty second tile
    
    ld de, W_WindowManager_CompositionArea
    
.startCompositionSecond
    ld [W_WindowManager_CompositionState], a
    
    ;Determine if we even need to write the second tile...
    ld a, b
    and a
    jr z, .cleanupAndReturn
    
    ;Ok, we do need to compose the second tile.
    ;Invert the mask and shiftcount
    ld a, 8
    sub b
    ld b, a
    ld a, c
    cpl
    ld c, a
    
    ;Actually recompose the second tile...
    ld hl, W_PatchUtils_FileBuffer
    ld a, 16
    
.compoLoopSecond
    push af
    push bc ;b = shift count, c = mask
    
    ;Mask off the existing composition data.
    ld a, [de]
    and c
    ld c, a
    
    ;Shift in the new composition data.
    ld a, [hli]
    
    bit 0, b
    jr z, .secondBitSecond
    sla a
    
.secondBitSecond
    bit 1, b
    jr z, .thirdBitSecond
    sla a
    sla a
    
.thirdBitSecond
    bit 2, b
    jr z, .composeLineSecond
    sla a
    sla a
    sla a
    sla a
    
    ;Mix both characters and store the composed data.
.composeLineSecond
    or c
    ld [de], a
    inc de
    
    pop bc
    pop af
    dec a
    jr nz, .compoLoopSecond
    
    ;Second tile's composed. Write more bits...
    ld a, [W_WindowManager_CompositionState]
    bit 3, a
    jr nz, .reverseEndingWriteback
    
.noReverseEndingWriteback
    set 2, a ;Dirty second tile
    jr .finalizeCompoState

.reverseEndingWriteback
    set 1, a ;Dirty first tile
    
.finalizeCompoState
    ld [W_WindowManager_CompositionState], a

.cleanupAndReturn
    pop af
    pop bc
    pop de
    pop hl
    
    ret
    
;ADVICE code for PrintText, called when printing a normal character.
WindowManager_ADVICE_PrintChara::
    ;Determine if VWF is active
    ld a, BANK(W_WindowManager_CompositionState)
    ld [REG_SVBK], a
    
    ld a, [W_WindowManager_CompositionState]
    and a ;equiv to cp M_WindowManager_CompositionStateUninitialized
    jp nz, .useVwf
    
.useTiletext
    call LCDC_PokeTilemap
    
    ld a, [W_LCDC_PokeTileX]
    inc a
    ld [W_LCDC_PokeTileX], a
    
    ret
    
.useVwf
    ld a, [W_WindowManager_VWFRingWriteHead]
    add $80
    ld [H_LCDC_SetTileVal], a
    call LCDC_PokeTilemap
    
    dec bc
    ld a, [bc] ;this better not be banked...
    inc bc
    call WindowManager_ADVICE_ComposeCharacter
    call WindowManager_ADVICE_FlushCompositionArea
    
    ld a, 6 ;TODO: Actually use a VWF table for this...
    call WindowManager_ADVICE_IncrementRingByPixels
    and a
    jr z, .noNewVwfTile
    
.newVwfTile
    ld a, [W_LCDC_PokeTileX]
    inc a
    ld [W_LCDC_PokeTileX], a
    
    ld a, [W_WindowManager_VWFRingWriteHead]
    ld [H_LCDC_SetTileVal], a
    call LCDC_PokeTilemap
    
.noNewVwfTile
    ret
    
;Configure the VWF.
;Once configured, all existing VWF state (if any) will be reset.
;
;ARGUMENTS: (Via Datastack)
; Composition Font (File ID)
; Background Color (16 bits of graphics data, to be repeated across all lines)
; VWF Ring Start   (Tile index from $8800)
; VWF Ring End     (Tile index from $8800)
; --- TOP OF STACK ---
WindowManager_ADVICE_OpVWFCONFIG::
    ld a, BANK(W_WindowManager_CompositionState)
    ld [REG_SVBK], a
    
    ;Configure the ring buffer from arguments.
    call BugVM_PopTypedData
    ld a, c
    ld [W_WindowManager_VWFRingEnd], a
    
    call BugVM_PopTypedData
    ld a, c
    ld [W_WindowManager_VWFRingStart], a
    ld [W_WindowManager_VWFRingWriteHead], a
    
    ;Configure the background. These 16 bits are repeated to clear tiles.
    call BugVM_PopTypedData
    ld a, c
    ld [W_WindowManager_CompositionBackground], a
    ld a, b
    ld [W_WindowManager_CompositionBackground + 1], a
    
    ;Initialize the composition area with the new background.
    ld hl, W_WindowManager_CompositionArea
    REPT 16
    ld a, c
    ld [hli], a
    ld a, b
    ld [hli], a
    ENDR
    
    ;Set the font from datastack args.
    call BugVM_PopTypedData
    ld a, c
    ld [W_WindowManager_CompositionFont], a
    ld a, b
    ld [W_WindowManager_CompositionFont + 1], a
    
    ;Mark the VWF as initialized and ready to use.
    ld a, M_WindowManager_CompositionStateIntialized
    ld [W_WindowManager_CompositionState], a
    
    xor a
    ld [W_WindowManager_CompositionShift], a
    
    ret
WindowManager_ADVICE_END::