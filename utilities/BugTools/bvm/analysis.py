from BugTools.exceptions import CircularEquateError
from BugTools.bvm.parser import SymbolicRef, Label, Instruction

def statically_prove_str(parselist, known_equates, start, end, indirslot = 0x172, indirslot_name = "W_MainScript_PortraitID", strval = 0xFFFF):
    """Prove if a BugVM program executes with memory set to a given value.
    
    start and end are the parselist indicies of the region of code we care
    about checking. indirslot is the BugVM immediate value pointing to the
    memory slot we want to check. strval is the value that we are checking to
    validate.
    
    known_equates is the list of known equates; this function expects all
    equates to have been resolved to a Python value and labels to be included
    within the list.
    
    This function will only return TRUE if it can be statically proven that the
    given memory slot is equal to the given value for the entire length of the
    given region. FALSE does not necessarily mean that the given assertion is
    logically false, merely that we could not prove it. The following are
    possible reasons why this process could fail:
    
    1. The program actually fails the given assertion
    2. No STR opcode writes to this memory slot
    3. A STR opcode does write to this memory slot, but it writes another INDIR
    or PRED value
    4. A STR opcode does write the given value to the memory slot, but it's
    obfuscated in some way that our static prover cannot handle
    5. A STR opcode does write the given value to the memory slot, but it's
    before a label or a jump instruction (cannot statically prove execution
    flow reaches the STR)
    6. A STR opcode does write the given value to the memory slot, but it does
    so after the start of the code region. Be conservative with your start
    and end indicies!
    7. Your code contains a label
    
    Basically we're only good for instruction streams like:
    
    IMMED $172
    INDIR
    IMMED $FFFF
    STR"""
    
    static_datastack = []
    proven_before_start = False
    ptr = 0
    while ptr < start and ptr < len(parselist):
        if type(parselist[ptr]) == Label:
            #Cannot guarantee execution flow across labels.
            static_datastack = []
            proven_before_start = False
        
        if type(parselist[ptr]) == Instruction:
            if parselist[ptr].opcode in ["JMPT", "JMP", "FARJMP"]:
                #Cannot guarantee execution flow across jumps.
                static_datastack = []
                proven_before_start = False
            
            if parselist[ptr].opcode in ["IMMED"]:
                if type(parselist[ptr].operands[0]) is SymbolicRef:
                    if parselist[ptr].operands[0].name == indirslot_name:
                        static_datastack.append(indirslot)
                    else:
                        static_datastack.append(0)
                else:
                    static_datastack.append(parselist[ptr].operands[0])
            
            if parselist[ptr].opcode in ["INDIR"] and len(static_datastack) > 0:
                static_datastack[-1] |= 0x10000 #Yes, this is how we tell immed and pred apart...
            
            if parselist[ptr].opcode in ["STR"]:
                if len(static_datastack) >= 2:
                    if static_datastack[-2] == indirslot | 0x10000:
                        proven_before_start = static_datastack[-1] == strval
                else:
                    proven_before_start = False
        
        ptr += 1
    
    if not proven_before_start:
        return False
    
    #At this point we have proven the region of code starts with a valid assertion
    #We just have to verify that the code region does not contain an STR that
    #would violate this invariant
    static_datastack = []
    ptr = start
    while ptr < end and ptr < len(parselist):
        if type(parselist[ptr]) == Label:
            #Cannot guarantee execution flow across labels.
            return False
        
        if type(parselist[ptr]) == Instruction:
            #Strictly speaking, a jump cannot break the invariant within the
            #region, so we won't return False on it.
            
            if parselist[ptr].opcode in ["IMMED"]:
                if type(parselist[ptr].operands[0]) is SymbolicRef:
                    if parselist[ptr].operands[0].name == indirslot_name:
                        static_datastack.append(indirslot)
                    else:
                        static_datastack.append(0)
                else:
                    static_datastack.append(parselist[ptr].operands[0])
            
            if parselist[ptr].opcode in ["INDIR"] and len(static_datastack) > 0:
                static_datastack[-1] |= 0x10000 #Yes, this is how we tell immed and pred apart...
            
            if parselist[ptr].opcode in ["STR"]:
                if len(static_datastack) >= 2:
                    if static_datastack[-2] == indirslot & 0x10000:
                        if static_datastack[-1] != strval:
                            #Invariant violated within code block.
                            return False
                else:
                    #Could not statically determine parameters to STR
                    return False
        
        ptr += 1
    
    return True

def resolve_instruction_operands(instr, known_equates, last_global):
    """Attempt to resolve SymbolicRefs in instructions.

    Returns the instruction with any SymbolicRefs changed to concrete values.
    If a SymbolicRef is unresolvable it will be left in the instruction."""
    resolved_operands = []

    for operand in instr.operands:
        if type(operand) is SymbolicRef:
            try:
                if operand.is_local:
                    resolved_operands.append(known_equates[last_global.symbol.name + operand.name])
                else:
                    resolved_operands.append(known_equates[operand.name])
            except KeyError:
                resolved_operands.append(operand)
        else:
            resolved_operands.append(operand)

    return resolved_operands
