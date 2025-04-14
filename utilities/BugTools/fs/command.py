from BugTools.fs.parser import bfs_grammar, BFSVisitor
from BugTools.fs.depstring import depstring
from BugTools.fs.fsimage import fsimage

import argparse, sys

def bfsbuild():
    parser = argparse.ArgumentParser(description='Tools for compiling a BugFS filesystem image and embedding it into a ROM.')

    parser.add_argument('infile', metavar='file.bfs', type=str, help='The directory listing to use.')
    parser.add_argument('outfile', metavar='file.bfsasm', type=str, help='Where to store the RGBDS object file for the BugFS image.')
    parser.add_argument('--basedir', metavar='build', type=str, action="append", help='Where to pull included files from.')

    args = parser.parse_args()

    with open(args.infile) as srcfile:
        src = srcfile.read()
        tree = bfs_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

        mp = BFSVisitor().visit(tree)

        datum = fsimage(mp, args.basedir)

        with open(args.outfile, 'w') as dstfile:
            dstfile.write(datum)

def bfsdeps():
    parser = argparse.ArgumentParser(description='Tool for extracting a list of dependencies from a .bfs file (for Make).')

    parser.add_argument('infile', metavar='file.bfs', type=str, help='The directory listing to use.')
    parser.add_argument('--basedir', metavar='build', type=str, action="append", help='Base directories to prefix each path. The first path will be used exclusively in the case of missing files and should form the "build directory".')

    args = parser.parse_args()

    with open(args.infile) as srcfile:
        src = srcfile.read()
        tree = bfs_grammar.parse(src + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

        mp = BFSVisitor().visit(tree)

        print(depstring(mp, args.basedir))
