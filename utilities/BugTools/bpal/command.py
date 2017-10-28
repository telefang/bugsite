from BugTools.bpal.parser import bpal_grammar, PaletteDataVisitor
from BugTools.bpal.passes import palette_encode

import argparse, sys

def bpalasm():
    parser = argparse.ArgumentParser(description="An assembler and source format for palette data in KAZe developed Game Boy games.")
    
    parser.add_argument("infile", metavar="file.bpal", type=str, help='The palette data to assemble.')
    parser.add_argument('output', metavar='file.palette.bin', type=str, help='Where to save the assembled palette colors.')
    
    args = parser.parse_args()
    
    with open(args.infile) as srcfile:
        src = srcfile.read()
        tree = bpal_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.
        
        mp = PaletteDataVisitor().visit(tree)
        
        pdata = palette_encode(mp)
        
        with open(args.output, "wb") as outfile:
            outfile.write(pdata)