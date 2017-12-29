from BugTools.banim.instructions import opcodes
from BugTools.banim.passes import default_keq
from BugTools.bvm.parser import Label, SymbolicRef, Instruction

import struct

LE16 = struct.Struct("<H")
BYTE = struct.Struct("<B")

mnemonics = {v: k for k, v in opcodes.items()}

def disassemble_spranim_file(banim_file):
    """Disassemble a sprite animation.
    
    Returns a parse list (to be unparsed by BugTools.bvm.formatting.unparse_bvm)"""
    
    parse_list = []
    labels = {}
    
    banim_file.seek(0)
    
    loop_loc = LE16.unpack(banim_file.read(2))[0]
    labels[0] = {"parselist": [Instruction("START", [SymbolicRef("loop_%X" % loop_loc, False)], "")],
                 "end": 2}
    labels[loop_loc] = {"parselist": [Label(SymbolicRef("loop_%X" % loop_loc, False), False)],
                        "end": loop_loc}
    
    banim_file.seek(loop_loc)
    
    frames = []
    
    #Step 1: Disassemble the animation loop
    try:
        while True:
            next_instr = BYTE.unpack(banim_file.read(1))[0]
            try:
                mnemonic = mnemonics[next_instr]
            except KeyError:
                mnemonic = "ENOP"
                
                if next_instr < 0x30 or next_instr >= 0x80:
                    mnemonic = "EFGAME"
                
                labels[loop_loc]["parselist"].append(Instruction(mnemonic, [next_instr], ""))
                continue
            
            if mnemonic == "FRAME":
                frame_loc = LE16.unpack(banim_file.read(2))[0]
                operand = [SymbolicRef("frame_%X" % frame_loc, False)]
                frames.append(frame_loc)
            elif mnemonic == "WAIT":
                operand = [BYTE.unpack(banim_file.read(1))[0]]
            else:
                operand = []
            
            labels[loop_loc]["parselist"].append(Instruction(mnemonic, operand, ""))
            
            if mnemonic in ["CLRESET", "RESET"]:
                break
    except struct.error:
        #eof reached
        #TODO: What happens if we EOF in the middle of an instruction?
        pass
    
    labels[loop_loc]["end"] = banim_file.tell()
    
    #Step 2: Disassemble each spritegroup
    for frame_loc in frames:
        banim_file.seek(frame_loc)
        
        frame_parselist = [Label(SymbolicRef("frame_%X" % frame_loc, False), False), Instruction("SPRITEGROUP", [], "")]
        
        try:
            length = BYTE.unpack(banim_file.read(1))[0] + 1
            
            for i in range(0, length):
                operand = []
                operand.append(BYTE.unpack(banim_file.read(1))[0]) #sprite X
                operand.append(BYTE.unpack(banim_file.read(1))[0]) #sprite Y
                operand.append(BYTE.unpack(banim_file.read(1))[0]) #sprite tile
                operand.append(BYTE.unpack(banim_file.read(1))[0]) #sprite attrs
                
                if operand[3] & 0x08 != 0: #opposite-bank tiles get renumbered
                    operand[3] ^= 0x08
                    operand[2] ^= 0x80
                
                for bitname, bitval in default_keq.items():
                    if operand[3] & bitval != 0:
                        operand[3] ^= bitval
                        operand.append(SymbolicRef(bitname, False))
                
                frame_parselist.append(Instruction("SPRITE", operand, ""))
        except struct.error:
            #eof'd
            pass
        
        frame_parselist.append(Instruction("ENDSPRITEGROUP", [], ""))
        
        labels[frame_loc] = {"parselist": frame_parselist,
                             "end": banim_file.tell()}
    
    #Step 3: Find garbage data in holes
    sorted_entry_points = list(labels.keys())
    sorted_entry_points.sort()
    for index, entry in enumerate(sorted_entry_points):
        if index == len(sorted_entry_points) - 1:
            #Look for data off the end of the last bit of the file
            banim_file.seek(0, 2)
            end = banim_file.tell()
        else:
            end = sorted_entry_points[index + 1]
        
        if (end - labels[entry]["end"]) > 0:
            bytes_missing = end - labels[entry]["end"]
            banim_file.seek(labels[entry]["end"])
            
            operand = []
            
            for i in range(0, bytes_missing):
                operand.append(BYTE.unpack(banim_file.read(1))[0])
            
            labels[entry]["parselist"].append(Instruction("DB", operand, ""))
            labels[entry]["end"] = banim_file.tell()
    
    #Step 4: Merge all the parselists together
    parselist = []
    for index, entry in enumerate(sorted_entry_points):
        parselist += labels[entry]["parselist"]
    
    return parselist