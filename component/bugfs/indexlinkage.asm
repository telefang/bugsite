SECTION "BugFS Indexing", ROM0[$09A4]
;Index the BugFS directory for a given file ID (BC).
;Returns the pointer to that file entry in the directory (HL) and sets the
;current ROM bank to the bank which holds that part of the directory.
;Not bank safe.
BugFS_IndexDirectory::
    ld a, b
    srl a
    srl a
    srl a
    and 1
    add a, BANK(BugFS_Directory)
    rst 0
    
    ld l, c
    ld a, b
    and 7
    ld h, a
    sla l
    rl h
    sla l
    rl h
    sla l
    rl h
    
    ld a, BugFS_Directory >> 8
    add a, h
    ld h, a
    
    ret