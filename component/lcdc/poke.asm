INCLUDE "bugsite.inc"

SECTION "LCDC Poke Configuration 2", WRAM0[$C4E0]
W_LCDC_SetAttrVal:: ds 2

SECTION "LCDC Poke Configuration", WRAM0[$C4EA]
W_LCDC_PokeTileX:: ds 2
W_LCDC_PokeTileY:: ds 2

SECTION "LCDC Poke", ROM0[$C7F]

;Given a screen coordinate in PokeTileX and PokeTileY, set the tile that covers
;the particular coordinate to SetTileVal, and it's attributes to SetAttrVal.
LCDC_PokeTilemap::
    ld a, 1
    ldh [H_LCDC_OAMNeedsStaging], a

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

    ld a, 0
    ldh [REG_VBK], a

    di

.wait1
    ldh a, [REG_STAT]
    and 2
    jr z, .wait1

.wait2
    ldh a, [REG_STAT]
    and 2
    jr nz, .wait2

    ldh a, [H_LCDC_SetTileVal]
    ld [hl], a

    ld a, 1
    ldh [REG_VBK], a

    ld a, [W_LCDC_SetAttrVal]
    ld [hl], a

    ei

    ld a, 0
    ldh [H_LCDC_OAMNeedsStaging], a
    ret