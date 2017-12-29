from BugTools.banim.instructions import opcodes

from BugTools.bvm.parser import Equate, SymbolicRef, Label, Instruction
from BugTools.bvm.object import Bof1, Bof1Patch, Bof1Symbol, Bof1PatchExpr
from BugTools.bvm.analysis import resolve_instruction_operands

default_keq = {
    "behindbg": 0x80,
    "vflip": 0x40,
    "hflip": 0x20
}

def fix_labels(parselist, known_equates = None):
    """Given a list of .banim commands, find the final positions of all labels.

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

    #We don't have support for SECTIONs yet, so we assume each .banim completely
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

            if command.opcode in ["SPRITE"]:
                instr_len += 3 #no opcode for sprite
            elif command.opcode in ["FRAME"]:
                instr_len += 2
            elif command.opcode in ["WAIT", "START"]:
                instr_len += 1 #no opcode for start, spritegroup
            elif command.opcode in ["ENDSPRITEGROUP"]:
                instr_len = 0 #this isn't an actual instruction, just a marker
            elif command.opcode in ["DB"]:
                instr_len -= 1 #DB in .banim isn't an opcode, just a language construct
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
                    elif type(operand) is bytes:
                        instr_len += len(operand)
                    else:
                        raise InvalidOperandError(command)

                #finally, account for the null terminator
                instr_len += 1

            pc_offset += instr_len

    return parselist, known_equates

def encode_sprite_animation(parselist, known_equates = None):
    """Given a list of .banim commands, encode the final instruction stream.

    This function will return the parse list, known equates list, and the
    resulting Bof1 object.

    String data is not permitted in DB opcodes, just byte data."""

    if known_equates is None:
        known_equates = {}
    else:
        known_equates = copy.deepcopy(known_equates)

    encoded_stream = []
    encoded_offset = 0

    bofdata = Bof1()
    mentioned_symbols = {}

    last_global = Label(SymbolicRef('', False), False)
    last_spritegroup_len = 0
    last_spritegroup_pos = None

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
                        encoded_offset += 1
                    elif type(operand) is SymbolicRef:
                        raise CircularEquateError(operand.name)
                    else:
                        raise InvalidOperandError(command)
            else:
                if command.opcode not in ["START", "SPRITEGROUP", "SPRITE", "ENDSPRITEGROUP"]:
                    try:
                        encoded_stream.append(bytes([opcodes[command.opcode]]))
                        encoded_offset += 1
                    except KeyError:
                        raise InvalidOpcodeError(command)

                if command.opcode in ["SPRITE"]:
                    sprdata = []

                    for operand in resolved_operands:
                        if len(sprdata) < 3:
                            if type(operand) is int:
                                sprdata.append(operand & 0xFF)
                            elif type(operand) is SymbolicRef:
                                #TODO: what exactly do we do with symbolic refs here?
                                sprdata.append(0x00)
                        else:
                            #attribs stuff...
                            if len(sprdata) < 4:
                                sprdata.append(0x00) #we fill this in later

                            if type(operand) is int:
                                #allow direct attributes
                                #this is intended mainly for use as palette data
                                #but we don't restrict it to the lower 3 bits
                                sprdata[3] ^= operand & 0xFF
                            elif type(operand) is SymbolicRef:
                                #TODO: what exactly do we do with symbolic refs here?
                                sprdata.append(0x00)

                    #It's possible to have less than 4 data items for a sprite,
                    #so fill everything else in with zeroes
                    while len(sprdata) < 4:
                        sprdata.append(0x00)

                    #TODO: is this the best way to represent sprites with more
                    #than 0x80 tiles? this will only work if such sprites get
                    #loaded into slot 0...
                    if sprdata[2] & 0x80 != 0:
                        sprdata[2] ^= 0x80
                        sprdata[3] ^= 0x08

                    encoded_stream.append(bytes(sprdata))
                    encoded_offset += len(sprdata)

                    last_spritegroup_len += 1
                elif command.opcode in ["SPRITEGROUP"]:
                    last_spritegroup_len = 0
                    last_spritegroup_pos = len(encoded_stream)

                    encoded_stream.append(bytes[0x00])
                    encoded_offset += 1
                elif command.opcode in ["ENDSPRITEGROUP"]:
                    #This command just exists to fixup the start of the spritegroup.
                    #Otherwise, we'd have to run a whole 'nother pass just to
                    #discover the length of each spritegroup.
                    encoded_stream[last_spritegroup_pos] = bytes([last_spritegroup_len])

                    last_spritegroup_len = 0
                    last_spritegroup_pos = None
                elif command.opcode in ["FRAME", "START"]: #commands with 16b operands
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
                elif command.opcode in ["WAIT"]: #commands with 8b operands
                    if len(resolved_operands) != 1:
                        raise InvalidOperandError(command)

                    for operand in resolved_operands:
                        if type(operand) is int:
                            encoded_stream.append(bytes([operand & 0xFF]))
                            encoded_offset += 1
                        else:
                            raise InvalidOperandError(command)
                elif command.opcode == "DB":
                    #This is the only command that accepts variable operands...
                    for operand in resolved_operands:
                        if type(operand) is int:
                            encoded_stream.append(bytes([operand & 0xFF]))
                            encoded_offset += 1
                        elif type(operand) is bytes:
                            encoded_stream.append(operand)
                            encoded_offset += len(operand)
                        else:
                            raise InvalidOperandError(command)

                    encoded_stream.append(bytes([0]))
                    encoded_offset += 1
                else:
                    #No other commands accept operands.
                    if len(resolved_operands) != 0:
                        raise InvalidOperandError(command)

    bofdata.data = b"".join(encoded_stream)

    return (parselist, known_equates, bofdata)
