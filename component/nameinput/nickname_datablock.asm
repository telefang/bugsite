INCLUDE "bugsite.inc"

;These variables are currently split because we can't do pointer maths from the
;BVM side yet. What we should be doing is having includes defining offsets into
;the block, but BVM doesn't support math expressions yet.
SECTION "Name Input Nickname Data Block", WRAM0[$CC00]
W_NameInput_NicknameDataBlock:: ds 48
W_NameInput_NicknameDataInputName:: ds 16

;TODO: Disassembly of the "nickname" data block opcodes.