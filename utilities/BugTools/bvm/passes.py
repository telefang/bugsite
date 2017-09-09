from BugTools.bvm.instructions import opcodes
from BugTools.bvm.parser import Equate, SymbolicRef, Label, Instruction
from BugTools.exceptions import LocalSymbolError, CircularEquateError, InvalidOperandError, InvalidOpcodeError

import itertools, copy

def resolve_equates(parselist, known_equates = None):
    """Given a list of .bvm commands, resolve all Equate values.

    Return value consists of the same parselist as well as an updated list of
    equates. Original parselist and equates are unmodified."""

    if known_equates is None:
        known_equates = {}
    else:
        known_equates = copy.deepcopy(known_equates)

    unresolved_equates = []

    for command in parselist:
        if type(command) == Equate:
            unresolved_equates.append(command)

    while len(unresolved_equates) > 0:
        for equate in unresolved_equates:
            if type(equate.value_expr) is not SymbolicRef:
                unresolved_equates.remove(equate)
                known_equates[equate.symbol.name] = equate.value_expr

                break
            elif type(equate.value_expr) is SymbolicRef and equate.value_expr.name in known_equates.keys():
                unresolved_equates.remove(equate)
                known_equates[equate.symbol.name] = known_equates[equate.value_expr.name]

                break
        else:
            if len(unresolved_equates) > 0:
                raise CircularEquateError([equate.symbol.name for equate in unresolved_equates])

    return parselist, known_equates

def fix_labels(parselist, known_equates = None, string_enc = None):
    """Given a list of .bvm commands, find the final positions of all labels.

    Labels will be added to the known equates list as if they were defined by
    EQU macros.

    All equates used by variable-length instructions (e.g. DB) must be known
    before fixing labels. If an instruction whose length depends on an
    unresolved equate value is detected, this function raises
    CircularEquateError."""

    if known_equates is None:
        known_equates = {}
    else:
        known_equates = copy.deepcopy(known_equates)

    #We don't have support for SECTIONs yet, so we assume each .bvm completely
    #assembles a single entry in the linkage directory. Labels are thus
    #exclusively program counter offsets, no linkage index yet.
    pc_offset = 0

    #We also have to resolve global labels.
    last_global_label = Label(SymbolicRef('', False), False)

    for command in parselist:
        if type(command) is Label:
            if command.symbol.is_local:
                if last_global_label is None:
                    #TODO: Raise LocalSymbolError when local label has no global
                    pass
                else:
                    known_equates[last_global_label.symbol.name + command.symbol.name] = pc_offset
            else:
                last_global_label = command
                known_equates[command.symbol.name] = pc_offset
        elif type(command) is Instruction:
            instr_len = 1

            if command.prefix == "NPREF":
                instr_len += 1

            if command.opcode in ["JMPT", "JMP", "JAL", "IMMED"]:
                instr_len += 2
            elif command.opcode in ["DB"]:
                for operand in command.operands:
                    if type(operand) is SymbolicRef:
                        try:
                            if operand.is_local:
                                operand = known_equates[last_global_label.symbol.name + operand.name]
                            else:
                                operand = known_equates[operand.name]
                        except KeyError:
                            raise CircularEquateError(operand.name)

                    if type(operand) is int:
                        instr_len += 1 #TODO: tag ints so we know what size they are...
                    elif type(operand) is str:
                        instr_len += len(string_enc(operand))
                    elif type(operand) is bytes:
                        instr_len += len(operand)
                    else:
                        raise InvalidOperandError(command)

                #finally, account for the null terminator
                instr_len += 1

            pc_offset += instr_len

    return parselist, known_equates

def statically_prove_str(parselist, known_equates, start, end, indirslot = 0x172, strval = 0xFFFF):
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

def autobalance_strings(parselist, known_equates, string_enc):
    """Optional pass to automatically word-wrap string equates used in text.
    
    This pass should run after equates have been resolved and labels fixed.
    It returns the given parselist and a new equates dictionary that has had
    autobalance applied to applicable strings.
    
    A set of DB opcodes referencing string equates set to empty string will
    cause those equates to be autobalanced. The whole run of empty string
    equates, including the last non-empty string equate, will be treated as a
    single 'autobalance set'. The instruction content of the given set of
    instructions will be modified to a series of DB, PRINT, and WINBRK
    instructions.
    
    Autobalance sets will not be processed if they contain instructions other
    than those normally used for dialogue management, namely DB, PRINT, POPALL,
    ARFREE, WINBRK, WINCLR, and WINWAIT opcodes.
    
    Furthermore, we assume the window width is the lowest possible for Bugsite.
    If we can statically determine from the parselist that these string equates
    are only used while indirect slot $172 is $FFFF, then we will use the wider
    portraitless window width for that autobalance set. Note that these are
    Bugsite specific and this autobalance routine cannot be used for other
    games that use BugVM, such as Zok Zok Heroes."""
    
    #First, we identify our autobalance groups.
    ab_groups = []
    next_ab_group = None
    last_global = Label(SymbolicRef('', False), False)

    for index, instr in enumerate(parselist):
        if type(instr) is Label:
            if not instr.symbol.is_local:
                last_global = instr
        
        if type(instr) is not Instruction:
            continue
        
        if instr.opcode == "DB" and len(instr.operands) > 0:
            if type(instr.operands[0]) is not SymbolicRef:
                #Autobalance groups can only be constructed from symbolic refs
                if next_ab_group is not None:
                    ab_groups.append(next_ab_group)
                    next_ab_group = None
                
                continue
            
            if instr.operands[0].is_local:
                target_symbol = known_equates[last_global.symbol.name + instr.operands[0].name]
            else:
                target_symbol = known_equates[instr.operands[0].name]
            
            if type(target_symbol) is not str:
                #Autobalance groups can only be constructed from string refs
                if next_ab_group is not None:
                    ab_groups.append(next_ab_group)
                    next_ab_group = None
                
                continue
            elif len(target_symbol) > 0:
                #Nonempty strings trigger a new autobalance group
                if next_ab_group is not None:
                    ab_groups.append(next_ab_group)
                    next_ab_group = None
                
                next_ab_group = [index]
            else:
                #Empty strings coalesce into the existing autobalance group
                next_ab_group.append(index)
        else:
            #Non-DB opcodes we don't care about
            continue
    else:
        #Clean up the last autobalance group
        if next_ab_group is not None:
            ab_groups.append(next_ab_group)
            next_ab_group = None
    
    new_streams = []

    #We now have a list of autobalance groups to consider.
    for ab_group in ab_groups:
        assert ab_group is not None
        
        #Assert autobalance group portrait state.
        has_no_portrait = statically_prove_str(parselist, known_equates, ab_group[0], ab_group[-1], 0x172, 0xFFFF)
        
        if has_no_portrait:
            ab_max_width = 16
        else:
            ab_max_width = 12
        
        #Collect our string data and break it into words
        merged_string = []
        for idx in ab_group:
            merged_string.append(known_equates[parselist[idx].operands[0].name])
            
        merged_string = "".join(merged_string)
        merged_bytes = string_enc(merged_string)

        newline = string_enc("\n")
        space = string_enc(" ")

        balanced_strings = []
        balanced_line = b""
        is_odd_line = True
        
        for line in merged_bytes.split(newline):
            for word in line.split(space):
                word = word.strip()
                
                if len(balanced_line) == 0:
                    balanced_line += word
                elif len(balanced_line) + len(space) + len(word) > ab_max_width:
                    balanced_strings.append(balanced_line)
                    balanced_line = word
                else:
                    balanced_line += space
                    balanced_line += word
            else:
                if len(balanced_line) > 0:
                    balanced_strings.append(balanced_line)
                    balanced_line = b""

        #Generate a new instruction stream for our now formatted string data.
        new_instruction_stream = []
        is_winbrk_line = False
        for line in balanced_strings:
            if is_winbrk_line:
                new_instruction_stream.append(Instruction("DB", [line], ""))
            else:
                new_instruction_stream.append(Instruction("DB", [line + newline], ""))

            new_instruction_stream.append(Instruction("PRINT", [], ""))
            new_instruction_stream.append(Instruction("ARFREE", [], ""))

            if is_winbrk_line:
                new_instruction_stream.append(Instruction("WINBRK", [], ""))

            is_winbrk_line = not is_winbrk_line
        else:
            #Remove the final PRINT, ARFREE, and WINBRK instruction
            if len(new_instruction_stream) > 0:
                if new_instruction_stream[-1].opcode == "WINBRK":
                    new_instruction_stream = new_instruction_stream[:-3]
                else:
                    new_instruction_stream = new_instruction_stream[:-2]
            else:
                new_instruction_stream = copy.deepcopy(parselist[ab_group[0]:ab_group[-1] + 1])
        
        new_streams.append(new_instruction_stream)

    out_parselist = copy.deepcopy(parselist)

    #We have to consider instruction stream replacement backwards because the
    #autobalance groups are discovered forwards, and replacing in the same
    #order would invalidate existing ar_group indicies.
    for ab_group, new_instruction_stream in zip(reversed(ab_groups), reversed(new_streams)):
        out_parselist = out_parselist[:ab_group[0]] + new_instruction_stream + out_parselist[ab_group[-1] + 1:]
    
    return (out_parselist, known_equates)

def resolve_instruction_operands(instr, known_equates, last_global):
    resolved_operands = []

    for operand in instr.operands:
        if type(operand) is SymbolicRef:
            try:
                if operand.is_local:
                    resolved_operands.append(known_equates[last_global.symbol.name + operand.name])
                else:
                    resolved_operands.append(known_equates[operand.name])
            except KeyError:
                raise CircularEquateError(operand.name)
        else:
            resolved_operands.append(operand)

    return resolved_operands

def encode_instruction_stream(parselist, known_equates = None, string_enc = None):
    """Given a list of .bvm commands, encode the final instruction stream.

    Due to the existence of the DB opcode, a string encoder is required to
    assemble them. Assembly will fail if a string encoder is not provided but
    the source code specifies a DB with a string.

    This function will return the parse list, known equates list, and the
    encoded instruction stream."""

    if known_equates is None:
        known_equates = {}
    else:
        known_equates = copy.deepcopy(known_equates)

    encoded_stream = []
    last_global = Label(SymbolicRef('', False), False)

    for command in parselist:
        if type(command) is Label:
            if not command.symbol.is_local:
                last_global = command
        elif type(command) is Instruction:
            resolved_operands = resolve_instruction_operands(command, known_equates, last_global)
            
            if command.prefix == "NPREF":
                encoded_stream.append(bytes([opcodes[command.prefix]]))
            
            if command.opcode in ["ENOP", "PNOP", "UO", "EFGAME"]:
                if len(resolved_operands) != 1:
                    raise InvalidOperandError(command)

                for operand in resolved_operands:
                    if type(operand) is int:
                        encoded_stream.append(bytes([operand]))
                    else:
                        raise InvalidOperandError(command)
            else:
                try:
                    encoded_stream.append(bytes([opcodes[command.opcode]]))
                except KeyError:
                    raise InvalidOpcodeError(command)

                if command.opcode in ["JAL", "JMP", "JMPT", "IMMED"]:
                    if len(resolved_operands) != 1:
                        raise InvalidOperandError(command)

                    for operand in resolved_operands:
                        if type(operand) is int:
                            encoded_stream.append(bytes([operand & 0xFF, operand >> 8]))
                        else:
                            raise InvalidOperandError(command)
                elif command.opcode == "DB":
                    #This is the only command that accepts variable operands...
                    for operand in resolved_operands:
                        if type(operand) is int:
                            encoded_stream.append(bytes([operand & 0xFF]))
                        elif type(operand) is str:
                            encoded_stream.append(string_enc(operand))
                        elif type(operand) is bytes:
                            encoded_stream.append(operand)
                        else:
                            raise InvalidOperandError(command)

                    encoded_stream.append(bytes([0]))
                else:
                    #No other commands accept operands.
                    if len(resolved_operands) != 0:
                        raise InvalidOperandError(command)

    return (parselist, known_equates, string_enc, b"".join(encoded_stream))
