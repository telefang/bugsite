from BugTools.bvm.instructions import opcodes
from BugTools.bvm.parser import Equate, SymbolicRef, Label, Instruction
from BugTools.bvm.analysis import statically_prove_str, resolve_instruction_operands
from BugTools.bvm.strings import effective_strlen
from BugTools.bvm.object import Bof1, Bof1Patch, Bof1Symbol, Bof1PatchExpr

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
    next_ab_group = []
    last_global = Label(SymbolicRef('', False), False)

    for index, instr in enumerate(parselist):
        if type(instr) is Label:
            if not instr.symbol.is_local:
                last_global = instr
        
        if type(instr) is not Instruction:
            continue
        
        if instr.opcode == "DB" and len(instr.operands) > 0:
            ab_group_viable = len(next_ab_group) > 0
            
            if type(instr.operands[0]) is not SymbolicRef:
                #Autobalance groups can only be constructed from symbolic refs
                if ab_group_viable:
                    ab_groups.append(next_ab_group)
                
                next_ab_group = []
                continue
            
            symbol_name = instr.operands[0].name
            if instr.operands[0].is_local:
                symbol_name = last_global.symbol.name + symbol_name
            
            #Symbols starting with STR_nn where nn >= 0x95 are system strings
            #and cannot be formatted with this routine.
            try:
                if symbol_name[:4] == "STR_" and int(symbol_name.split("_")[1], 16) >= 0x95:
                    continue
            except ValueError:
                pass
            
            target_symbol = known_equates[symbol_name]
            
            if type(target_symbol) is not str:
                #Autobalance groups can only be constructed from string refs
                if ab_group_viable:
                    ab_groups.append(next_ab_group)
                
                next_ab_group = []
                continue
            elif len(target_symbol) > 0:
                #Nonempty strings trigger a new autobalance group
                if ab_group_viable:
                    ab_groups.append(next_ab_group)
                
                next_ab_group = [index]
                continue
            else:
                #Empty strings coalesce into the existing autobalance group
                next_ab_group.append(index)
        else:
            #Non-DB opcodes we don't care about
            continue
    else:
        #Clean up the last autobalance group
        if len(next_ab_group) > 0:
            ab_groups.append(next_ab_group)
    
    new_streams = []

    #We now have a list of autobalance groups to consider.
    for ab_group in ab_groups:
        assert ab_group is not None
        
        #Assert autobalance group portrait state.
        has_no_portrait = statically_prove_str(parselist, known_equates, ab_group[0], ab_group[-1], 0x172, 0xFFFF)
        
        if has_no_portrait:
            ab_max_width = 17 * 8
        else:
            ab_max_width = 12 * 8
        
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
                elif effective_strlen(balanced_line, string_enc) + effective_strlen(space, string_enc) + effective_strlen(word, string_enc) > ab_max_width:
                    #That condition uses visual, not physical length
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

def optimize_stream(parselist):
    """Given a list of .bvm commands, remove extraneous instructions.
    
    Extraneous is defined as any opcode with no effect. Notably, this removes
    PNOP and ENOP, allowing the insertion of new opcodes in patched BugVM
    games.
    
    Returns a duplicate parselist with extraneous instructions and prefixes
    removed."""
    
    new_parselist = []
    
    for instr in parselist:
        if type(instr) is Instruction and instr.opcode in ["PNOP", "ENOP"]:
            continue
        
        if type(instr) is Instruction and instr.prefix in ["NPREF"]:
            new_instr = copy.deepcopy(instr)
            instr.prefix = ""
            
            continue
        
        new_parselist.append(copy.deepcopy(instr))
    
    return new_parselist

def encode_instruction_stream(parselist, known_equates = None, string_enc = None, opcodes = opcodes):
    """Given a list of .bvm commands, encode the final instruction stream.

    Due to the existence of the DB opcode, a string encoder is required to
    assemble them. Assembly will fail if a string encoder is not provided but
    the source code specifies a DB with a string.

    This function will return the parse list, known equates list, and the
    resulting Bof1 object."""

    if known_equates is None:
        known_equates = {}
    else:
        known_equates = copy.deepcopy(known_equates)
    
    encoded_stream = []
    encoded_offset = 0
    
    bofdata = Bof1()
    mentioned_symbols = {}
    
    last_global = Label(SymbolicRef('', False), False)
    
    for command in parselist:
        if type(command) is Label:
            if not command.symbol.is_local:
                last_global = command
        elif type(command) is Instruction:
            resolved_operands = resolve_instruction_operands(command, known_equates, last_global)
            
            if command.prefix == "NPREF":
                encoded_stream.append(bytes([opcodes[command.prefix]]))
                encoded_offset += 1
            
            if command.opcode in ["ENOP", "PNOP", "UO", "EFGAME"]:
                if len(resolved_operands) != 1:
                    raise InvalidOperandError(command)
                
                for operand in resolved_operands:
                    if type(operand) is int:
                        encoded_stream.append(bytes([operand]))
                        encoded_offset += 1
                    elif type(operand) is SymbolicRef:
                        raise CircularEquateError(operand.name)
                    else:
                        raise InvalidOperandError(command)
            else:
                try:
                    encoded_stream.append(bytes([opcodes[command.opcode]]))
                    encoded_offset += 1
                except KeyError:
                    raise InvalidOpcodeError(command)

                if command.opcode in ["JAL", "JMP", "JMPT", "IMMED"]:
                    if len(resolved_operands) != 1:
                        raise InvalidOperandError(command)

                    for operand in resolved_operands:
                        if type(operand) is int:
                            encoded_stream.append(bytes([operand & 0xFF, operand >> 8]))
                            encoded_offset += 2
                        elif type(operand) is SymbolicRef:
                            encoded_stream.append(bytes([0x00, 0x00]))
                            if operand.name not in mentioned_symbols.keys():
                                bvmsym = Bof1Symbol()
                                bvmsym.name = operand.name
                                bvmsym.symtype = Bof1Symbol.IMPORT
                                
                                mentioned_symbols[operand.name] = len(bofdata.symbols)
                                bofdata.symbols.append(bvmsym)
                            
                            bvmpatch = Bof1Patch()
                            bvmpatch.patchoffset = encoded_offset
                            bvmpatch.patchtype = Bof1Patch.LE16
                            
                            bvmpexpr = Bof1PatchExpr()
                            bvmpexpr.__tag__ = Bof1PatchExpr.INDIR
                            bvmpexpr.INDIR = mentioned_symbols[operand.name]
                            
                            bvmpatch.patchexprs.append(bvmpexpr)
                            bofdata.patches.append(bvmpatch)
                            
                            encoded_offset += 2
                        else:
                            raise InvalidOperandError(command)
                elif command.opcode == "DB":
                    #This is the only command that accepts variable operands...
                    for operand in resolved_operands:
                        if type(operand) is int:
                            encoded_stream.append(bytes([operand & 0xFF]))
                            encoded_offset += 1
                        elif type(operand) is str:
                            opstr = string_enc(operand)
                            encoded_stream.append(opstr)
                            encoded_offset += len(opstr)
                        elif type(operand) is bytes:
                            encoded_stream.append(operand)
                            encoded_offset += len(operand)
                        else:
                            raise InvalidOperandError(command)

                    encoded_stream.append(bytes([0]))
                else:
                    #No other commands accept operands.
                    if len(resolved_operands) != 0:
                        raise InvalidOperandError(command)
    
    bofdata.data = b"".join(encoded_stream)
    
    return (parselist, known_equates, string_enc, bofdata)
