from BugTools.montable.extract import extract_bugnames_from_block
from BugTools.montable.parser import parse_names_list
from BugTools.montable.stringbuilder import build_string_object
from BugTools.bvm.strings import parse_charmap

import argparse, sys, csv

def montable_extract():
    parser = argparse.ArgumentParser(description='Extracts data from the monster tables in Network Adventure Bugsite.')

    parser.add_argument('infile', metavar='file.bvm', type=str, help='The file to extract from.')
    parser.add_argument('charmap', metavar='charmap.bin', type=str, help='Character mapping to decode with.')
    parser.add_argument('bank', metavar='4', type=int, help='What bank to extract from.')
    parser.add_argument('output', metavar='file.bugvm.bin', type=str, help='Where to save the assembled code.')

    args = parser.parse_args()

    with open(args.charmap, encoding="utf-8") as mapfile:
        strenc, strdec = parse_charmap(mapfile)

    with open(args.infile, "rb") as romfile:
        tabledata = extract_bugnames_from_block(romfile, args.bank, 0x4000 // 0x40, strdec)

    with open(args.output, "w", encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)

        for row in tabledata:
            encoded_row = [cell.encode('utf-8') for cell in row]
            csvwriter.writerow(row)

def montable_compile():
    parser = argparse.ArgumentParser(description='Compiles name data into the name slots of the attribute tables in Network Adventure Bugsite. Produces an RGBDS compatible object file.')

    parser.add_argument('infile', metavar='file.csv', type=str, help='The file to pull strings from.')
    parser.add_argument('charmap', metavar='charmap.bin', type=str, help='Character mapping to decode with.')
    parser.add_argument('output', metavar='file.atbl', type=str, help='Where to save the resulting compiled source.')
    parser.add_argument('--language', type=str, default=u"Japanese")

    args = parser.parse_args()

    with open(args.charmap, encoding="utf-8") as mapfile:
        strenc, strdec = parse_charmap(mapfile)

    with open(args.infile, encoding="utf-8") as infile:
        strlist = parse_names_list(infile, args.language)
        asmsrc = build_string_object(strlist, strenc)

    with open(args.output, "w") as rgbfile:
        rgbfile.write(asmsrc)
