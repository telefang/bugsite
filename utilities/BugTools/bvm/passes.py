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

def fix_labels(parselist, known_equates = None):
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
                        instr_len += len(operand) #we assume all characters take 1 byte to encode...
                    else:
                        raise InvalidOperandError(command)

                #finally, account for the null terminator
                instr_len += 1

            pc_offset += instr_len

    return parselist, known_equates

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
                            encoded_stream.append(bytes(operand))
                        elif type(operand) is str:
                            encoded_stream.append(string_enc(operand))
                        else:
                            raise InvalidOperandError(command)
                else:
                    #No other commands accept operands.
                    if len(resolved_operands) != 0:
                        raise InvalidOperandError(command)

    return (parselist, known_equates, string_enc, b"".join(encoded_stream))
