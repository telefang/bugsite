M_MainScript_CompositionStateUninitialized EQU 0
M_MainScript_CompositionStateIntialized EQU 1

;NOTE: These bits' names refer to the physical order of the tiles and their
;meaning does not change when the REVERSE bit is on.
M_MainScript_CompositionStateFirstTileDirty EQU 2
M_MainScript_CompositionStateSecondTileDirty EQU 4
M_MainScript_CompositionStateTileOrderReverse EQU 8