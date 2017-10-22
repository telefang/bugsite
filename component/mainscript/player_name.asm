INCLUDE "bugsite.inc"

SECTION "Main Script Player Name Memory", WRAM0[$C9F0]
W_MainScript_PlayerName:: ds 9 ;This size is a guess.

SECTION "Main Script Player Name", ROM0[$1652]
MainScript_PrintPlayerName::
    ld bc, W_MainScript_PlayerName
    call WindowManager_PrintText
    ret