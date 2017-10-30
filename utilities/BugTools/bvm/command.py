from BugTools.bvm.instructions import opcodes
from BugTools.bvm.parser import bvm_grammar, InstrListVisitor
from BugTools.bvm.passes import resolve_equates, fix_labels, autobalance_strings, optimize_stream, encode_instruction_stream, inflate_psuedoinstructions
from BugTools.bvm.formatting import unparse_bvm
from BugTools.bvm.strings import parse_stringtbl, parse_charmap

from BugTools.bfont.parser import bfont_grammar, FontWidthVisitor
from BugTools.bfont.passes import metrics_table, metrics_length

import argparse, sys, json

def bvmasm():
    parser = argparse.ArgumentParser(description='An assembler and source format for the BugVM virtual machine, commonly seen in KAZe developed Game Boy games.')

    parser.add_argument('infile', metavar='file.bvm', type=str, help='The file to assemble.')
    parser.add_argument('--deffile', dest='deffile', metavar='strings.csv', type=str, action='append', help='Macro equates for the .bvm code to use. Must be UTF-8.')
    parser.add_argument('--language', type=str, default=u"Japanese", help='Which language\'s equates should be used when reading definitions files')
    parser.add_argument('--autobalance', help='String equates larger than a single line will overflow into following empty equates.', action='store_true')
    parser.add_argument('--metrics', metavar='metrics.bfont', type=str, help='File detailing VWF metrics for this font.')
    parser.add_argument('--optimize', help='Remove extraneous instructions and prefixes.', action='store_true')
    parser.add_argument('--opcode_tbl', dest='opcode_tbl', metavar='opcodes.json', type=str, help='Mapping of instruction opcodes to their binary representations.')
    parser.add_argument('charmap', metavar='charmap.bin', type=str, help='Character mapping for the DB opcode.')
    parser.add_argument('output', metavar='file.bugvm.bin', type=str, help='Where to save the assembled code.')
    
    args = parser.parse_args()
    
    ke = {}
    
    for deffilename in args.deffile:
        with open(deffilename, encoding="utf-8") as strfile:
            ke.update(parse_stringtbl(strfile, args.language))
    
    opcode_tbl = opcodes
    if args.opcode_tbl is not None:
        with open(args.opcode_tbl, encoding="utf-8") as opfile:
            opcode_tbl = json.load(opfile)
    
    with open(args.charmap, encoding="utf-8") as mapfile:
        strenc, strdec = parse_charmap(mapfile)
        
    metrics = [8] * 0xFF #fallback in case we autobalance without a bfont file
    if args.metrics is not None:
        with open(args.metrics, encoding="utf-8") as metrfile:
            msrc = metrfile.read()
            mtree = bfont_grammar.parse(msrc + "\n")
            mparse = FontWidthVisitor().visit(mtree)

            metrics = metrics_table(mparse, strenc)
    
    string_wid = metrics_length(metrics, strenc)
    
    with open(args.infile) as srcfile:
        src = srcfile.read()
        tree = bvm_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.
        
        mp = InstrListVisitor().visit(tree)
        
        mp = inflate_psuedoinstructions(mp)
        
        mp, ke = resolve_equates(mp, ke)
        
        if args.autobalance:
            mp, ke = autobalance_strings(mp, ke, strenc, string_wid)
        
        if args.optimize:
            mp = optimize_stream(mp)
        
        mp, ke = fix_labels(mp, ke, strenc)
        mp, ke, strenc, bvmdata = encode_instruction_stream(mp, ke, strenc, opcode_tbl)

        with open(args.output, 'wb') as outfile:
            outfile.write(bvmdata.bytes)

def bvmfmt():
    parser = argparse.ArgumentParser(description='Reformats BVM source code to current formatting standards.')
    
    parser.add_argument('infile', metavar='file.bvm', type=str, help='The file to reformat.')
    parser.add_argument('charmap', metavar='charmap.bin', type=str, help='Character mapping.')
    
    args = parser.parse_args()
    
    with open(args.charmap, encoding="utf-8") as mapfile:
        strenc, strdec = parse_charmap(mapfile)
    
    with open(args.infile, encoding="utf-8") as srcfile:
        src = srcfile.read()
        tree = bvm_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.
        
        mp = InstrListVisitor().visit(tree)
    
    with open(args.infile, 'w', encoding="utf-8") as outfile:
        outfile.write(unparse_bvm(mp, strdec))