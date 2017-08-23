from BugTools.bvm.parser import bvm_grammar, InstrListVisitor
from BugTools.bvm.passes import resolve_equates, fix_labels, encode_instruction_stream
from BugTools.bvm.strings import parse_stringtbl, parse_charmap
from parsimonious.exceptions import IncompleteParseError

with open("../script/bugvm_strings.txt", encoding="utf-8") as strfile:
    ke = parse_stringtbl(strfile)

with open("../script/charmap.txt", encoding="utf-8") as mapfile:
    strenc, strdec = parse_charmap(mapfile)

with open("../script/unknown_bvm/1.bvm") as file:
    y = file.read()
    x = bvm_grammar.parse(y + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

    mp = InstrListVisitor().visit(x)

    mp, ke = resolve_equates(mp, ke)
    mp, ke = fix_labels(mp, ke)
    mp, ke, strenc, data = encode_instruction_stream(mp, ke, strenc) #TODO: actually encode strings...

    print (data)
