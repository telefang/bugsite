INCLUDE "bugsite.inc"

SECTION "Native Code Patch Table", ROMX[$6100], BANK[$3]
;Table of all patches in BANK 3.
;Patches themselves live from $6200-$7FFF in BANK 3, the largest contiguous
;free space run in the ROM.
;Each table entry consists of 4 bytes of executable code, usually a jump and a
;nop.
PatchSupport_PatchTable::
    ds $100