from BugTools.banim.instructions import opcodes
from BugTools.banim.passes import fix_labels, encode_sprite_animation, default_keq
from BugTools.banim.dis import disassemble_spranim_file
from BugTools.bvm.parser import bvm_grammar, InstrListVisitor
from BugTools.bvm.passes import resolve_equates
from BugTools.bvm.formatting import unparse_bvm

import argparse, sys, json

def banimasm():
    parser = argparse.ArgumentParser(description='An assembler and source format for SpriteManager animation data, commonly seen in KAZe developed Game Boy games.')

    parser.add_argument('infile', metavar='file.banim', type=str, help='The file to assemble.')
    parser.add_argument('output', metavar='file.spranim.bof', type=str, help='Where to save the assembled code.')

    args = parser.parse_args()

    ke = copy.deepcopy(default_keq)

    with open(args.infile) as srcfile:
        src = srcfile.read()
        tree = bvm_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

        mp = InstrListVisitor().visit(tree)

        mp, ke = resolve_equates(mp, ke)
        mp, ke = fix_labels(mp, ke, strenc)
        mp, ke, banimdata = encode_sprite_animation(mp, ke)

        with open(args.output, 'wb') as outfile:
            outfile.write(banimdata.bytes)

def disbanim():
    parser = argparse.ArgumentParser(description='A disassembler for SpriteManager animation data, commonly seen in KAZe developed Game Boy games.')

    parser.add_argument('infile', metavar='file.spranim.bof', type=str, help='The file to disassemble.')
    parser.add_argument('output', metavar='file.banim', type=str, help='Where to save the disassembled source.')

    args = parser.parse_args()

    with open(args.infile, 'rb') as srcfile:
        mp = disassemble_spranim_file(srcfile)
        
        with open(args.output, 'w') as outfile:
            outfile.write(unparse_bvm(mp, lambda inbytes: "".join(inbytes)))