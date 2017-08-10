from BugTools.bvm.parser import bvm_grammar, InstrListVisitor
from BugTools.bvm.passes import resolve_equates, fix_labels, encode_instruction_stream
from BugTools.bvm.strings import parse_stringtbl, parse_charmap

import argparse, sys

def bvmasm():
    parser = argparse.ArgumentParser(description='An assembler and source format for the BugVM virtual machine, commonly seen in KAZe developed Game Boy games.')

    parser.add_argument('infile', metavar='file.bvm', type=str, help='The file to assemble.')
    parser.add_argument('strings', metavar='strings.txt', type=str, help='String equates for the .bvm code to use. Must be UTF-16.')
    parser.add_argument('charmap', metavar='charmap.bin', type=str, help='Character mapping for the DB opcode.')
    parser.add_argument('output', metavar='file.bugvm.bin', type=str, help='Where to save the assembled code.')

    args = parser.parse_args()

    with open(args.strings, encoding="utf-8") as strfile:
        ke = parse_stringtbl(strfile)

    with open(args.charmap, encoding="utf-8") as mapfile:
        strenc = parse_charmap(mapfile)

    with open(args.infile) as srcfile:
        src = srcfile.read()
        tree = bvm_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

        mp = InstrListVisitor().visit(tree)

        mp, ke = resolve_equates(mp, ke)
        mp, ke = fix_labels(mp, ke)
        mp, ke, strenc, data = encode_instruction_stream(mp, ke, strenc)

        with open(args.output, 'wb') as outfile:
            outfile.write(data)
