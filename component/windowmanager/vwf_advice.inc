DEF M_WindowManager_CompositionStateUninitialized EQU 0
DEF M_WindowManager_CompositionStateInitialized EQU 1

;NOTE: These bits' names refer to the physical order of the tiles and their
;meaning does not change when the REVERSE bit is on.
DEF M_WindowManager_CompositionStateFirstTileDirty EQU 2
DEF M_WindowManager_CompositionStateSecondTileDirty EQU 4
DEF M_WindowManager_CompositionStateTileOrderReverse EQU 8