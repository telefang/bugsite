INCLUDE "bugsite.inc"

SECTION "LCDC vmemcopy", ROM0[$037C]
LCDC_vmemcopy::
    di
    
.memWait1
    ld a, [REG_STAT]
    and 2
    jr z, .memWait1
    
.memWait2
    ld a, [REG_STAT]
    and 2
    jr nz, .memWait2
    
    ld a, [hli]
    ld [de], a
    
    ei
    
    inc de
    dec bc
    ld a, b
    or c
    jr nz, LCDC_vmemcopy
    
    ret