INCLUDE "bugsite.inc"

SECTION "Patch Utils Read File Buffer", WRAMX[$DFF0], BANK[$2]
W_PatchUtils_FileBuffer:: ds M_PatchUtils_FileBufferSize

SECTION "Patch Utils ReadFile", ROM0[$0073]
;Read parts of a BugFS file into RAM.
;Patch code lives in ROM4, so we cannot read other banks' data. So copy what we
;need into some available RAM and work on it there. Set BC as your file's ID and
;DE the offset to copy from. M_PatchUtils_FileBufferSize (currently $10) bytes
;will transfer into W_PatchUtils_FileBuffer.
;This function is bank safe but makes no attempt at validating file size.
;
;ARGUMENTS: (Not preserved)
;  BC = BugFS file ID
;  DE = Copy offset

PatchSupport_ReadBugFSFile::
    push af
    push hl
    
    ldh a, [H_System_CurrentROMBank]
    push af
    
    ;Read the file location.
    call BugFS_IndexDirectory
    ld a, [hli]
    push af
    
    ld a, [hli]
    ld h, [hl]
    ld l, a
    
    add hl, de
    ld a, $40
    add a, h
    ld h, a
    
    pop af
    rst 0
    
    ld a, BANK(W_PatchUtils_FileBuffer)
    ldh [REG_SVBK], a
    
    ;Copy data.
    ld c, M_PatchUtils_FileBufferSize
    ld de, W_PatchUtils_FileBuffer
    
.copyLoop
    bit 7, h
    jr nz, .overflowHandler
    
    ld a, [hli]
    ld [de], a
    inc de
    dec c
    jr nz, .copyLoop
    jr .finishedCopying
    
    ;We reached the end of one bank.
    ;Move onto the next one.
.overflowHandler
    res 7, h
    set 6, h
    ldh a, [H_System_CurrentROMBank]
    inc a
    rst 0
    jr .copyLoop
    
    ;Restore ROM bank and unclobber non-argument registers.
.finishedCopying
    pop af
    rst $0
    
    pop hl
    pop af
    
    ret
PatchSupport_ReadBugFSFile_END::