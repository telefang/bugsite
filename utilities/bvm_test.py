from BugTools.bvm.parser import bvm_grammar, InstrListVisitor
from BugTools.bvm.passes import resolve_equates, fix_labels, encode_instruction_stream
from parsimonious.exceptions import IncompleteParseError

with open("../script/unknown_bvm/1.bvm") as file:
    y = file.read()
    x = bvm_grammar.parse(y + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

    mp = InstrListVisitor().visit(x)

    mp, ke = resolve_equates(mp)
    mp, ke = fix_labels(mp, ke)
    mp, ke = encode_instruction_stream(mp, ke, str) #TODO: actually encode strings...

    print (mp, ke)
