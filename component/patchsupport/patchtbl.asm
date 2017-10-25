INCLUDE "bugsite.inc"

SECTION "Native Code Patch Table", ROMX[$6100], BANK[$3]
;Table of all patches in BANK 3.
;Patches themselves live from $6200-$7FFF in BANK 3, the largest contiguous
;free space run in the ROM.
;Each table entry consists of 4 bytes of executable code, usually a jump and a
;ret.
PatchSupport_PatchTable::
Banked_WindowManager_ADVICE_OpVWFCONFIG::
    jp WindowManager_ADVICE_OpVWFCONFIG
    nop
    
    ds $2C ;Remaining bytes for custom opcodes.
    
Banked_WindowManager_ADVICE_PrintChara::
    jp WindowManager_ADVICE_PrintChara
    nop
    
Banked_WindowManager_ADVICE_PrintNewline::
    jp WindowManager_ADVICE_PrintNewline
    nop
    
Banked_WindowManager_ADVICE_AutoNewline::
    jp WindowManager_ADVICE_AutoNewline
    nop
    
Banked_WindowManager_ADVICE_ClearRegion::
    jp WindowManager_ADVICE_ClearRegion
    nop
    
    ds $C0