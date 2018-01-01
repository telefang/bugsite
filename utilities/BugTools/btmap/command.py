from BugTools.btmap.passes import read_btmap, serialize_tilemap
from BugTools.btmap.dis import unserialize_tilemap, write_btmap

import argparse

def btmapasm():
    parser = argparse.ArgumentParser(description="A compiler for tilemap files used by the disassembly project for Network Adventure Bugsite.")

    parser.add_argument("infile", metavar="normal.btmap.csv", type=str, help="The tilemap data to compile.")
    parser.add_argument("outfile", metavar="normal.tmap.bin", type=str, help="Where to save the resulting compiled tilemap.")

    args = parser.parse_args()

    with open(args.infile, encoding="utf-8") as infile:
        data = read_btmap(infile)

    with open(args.outfile, "wb") as outfile:
        outfile.write(serialize_tilemap(data))

def disbtmap():
    parser = argparse.ArgumentParser(description="A disassembler for tilemap files used by the disassembly project for Network Adventure Bugsite.")

    parser.add_argument("infile", metavar="normal.tmap.bin", type=str, help="The tilemap data to disassemble.")
    parser.add_argument("outfile", metavar="normal.btmap.csv", type=str, help="Where to save the resulting compiled tilemap.")

    args = parser.parse_args()

    with open(args.infile, "rb") as infile:
        data = unserialize_tilemap(infile)

    with open(args.outfile, "w", encoding="utf-8") as outfile:
        write_btmap(data, outfile)
