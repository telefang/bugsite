INCLUDE "bugsite.inc"

SECTION "Patch Support Custom BugVM Opcodes", ROM0[$0099]
;Implementation of all custom BugVM opcodes.
;We map the opcode table to the patch advice table, replacing ENOP $1F thru
;ENOP $2B with patches $0-$C. Note that this requires PNOP/ENOP to be removed
;in your .bvm, or for bvmasm to remove it for you.
PatchSupport_OpCustom::
    srl b
    rr c
    
    ld a, c
    sub $1F
    
    ld b, 0
    sla b
    rl c
    sla b
    rl c
    
    jp PatchSupport_PointCutByID
    
PatchSupport_OpCustom_END::