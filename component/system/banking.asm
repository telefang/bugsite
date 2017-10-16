INCLUDE "bugsite.inc"

SECTION "System Bank Util", ROM0[$0000]
System_SwitchBank:: ;usually called via rst $0
    di
    ld [REG_MBC5_ROMBank0], a
    ld [H_System_CurrentROMBank], a
    ei
    
    ret