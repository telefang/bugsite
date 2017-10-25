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
    
    ld a, [H_System_CurrentROMBank]
    push af
    
    ;Read the file location.
    call BugFS_IndexDirectory
    ld a, [hli]
    push af
    
    ld a, [hli]
    ld h, [hl]
    ld l, a
    
    add hl, de
    set 6, h ; or $4000
    
    pop af
    ld [REG_MBC5_ROMBank0], a
    
    ld a, BANK(W_PatchUtils_FileBuffer)
    ld [REG_SVBK], a
    
    ;Copy data.
    ld c, M_PatchUtils_FileBufferSize
    ld de, W_PatchUtils_FileBuffer
    
.copyLoop
    ld a, [hli]
    ld [de], a
    inc de
    dec c
    jr nz, .copyLoop
    
    ;Restore ROM bank and unclobber non-argument registers.
    pop af
    rst $0
    
    pop hl
    pop af
    
    ret
PatchSupport_ReadBugFSFile_END::