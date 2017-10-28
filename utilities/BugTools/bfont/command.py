from BugTools.bfont.parser import bfont_grammar, FontWidthVisitor
from BugTools.bfont.passes import metrics_table

from BugTools.bvm.strings import parse_charmap

import argparse, sys, json

def bfontmetrics():
    parser = argparse.ArgumentParser(description="A compiler for the font metrics files used by the English translation project for Network Adventure Bugsite.")
    
    parser.add_argument("infile", metavar="normal.bfont", type=str, help="The font specification file to compile.")
    parser.add_argument('charmap', metavar='charmap.bin', type=str, help='Character mapping for the current ROM.')
    parser.add_argument("outfile", metavar="normal.metrics", type=str, help="Where to save the resulting metrics data.")
    
    args = parser.parse_args()
    
    with open(args.charmap, encoding="utf-8") as mapfile:
        strenc, strdec = parse_charmap(mapfile)
    
    with open(args.infile, encoding="utf-8") as metrfile:
        msrc = metrfile.read()
        mtree = bfont_grammar.parse(msrc + "\n")
        mparse = FontWidthVisitor().visit(mtree)
        
        metrics = metrics_table(mparse, strenc)
    
    with open(args.outfile, "wb") as outfile:
        outfile.write(bytes(metrics))