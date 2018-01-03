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
    
Banked_WindowManager_ADVICE_OpVWFENABLE::
    jp WindowManager_ADVICE_OpVWFENABLE
    nop
    
Banked_WindowManager_ADVICE_OpVWFDISABLE::
    jp WindowManager_ADVICE_OpVWFDISABLE
    nop
    
    ds $24 ;Remaining bytes for custom opcodes.
    
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
    
Banked_WindowManager_ADVICE_PrintChoices::
    jp WindowManager_ADVICE_PrintChoices
    nop
    
Banked_WindowManager_ADVICE_OpSCRCURS::
    jp WindowManager_ADVICE_OpSCRCURS
    nop
    
Banked_WindowManager_ADVICE_OpWINCURS::
    jp WindowManager_ADVICE_OpWINCURS
    nop
    
    ds $B4