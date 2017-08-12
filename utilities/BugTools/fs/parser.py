from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor, Node

from BugTools.util import flatten

bfs_grammar = Grammar(
    """
    lines = _ line*
    line = (filename eol) / (label? filename? eol) / eol

    #These productions define what our data types look like.
    label = ~"[a-zA-Z_][a-zA-Z_0-9]*" ":" _
    filename = ~"[\'\\"][^\'\\"]*[\'\\"]"i _

    #This production exists entirely to ensure other productions don't try to
    #merge entire newlines together.
    eol = _? newline _?
    newline = ~"[\\r\\n]"

    #These productions pull whitespace and comments out of the parsetree
    _ = meaninglessness*
    meaninglessness = whitespace / comment
    comment = ~";[^\\r\\n]*"
    whitespace = ~"[ \t]+"
    """);

class Label(object):
    def __init__(self, symbol):
        self.symbol = symbol

    def __repr__(self):
        return "Label(%s)" % (repr(self.symbol),)

class Filename(object):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "Filename(%s)" % (repr(self.path),)

class BFSVisitor(NodeVisitor):
    """Converts a parsed .bfs directory into a list of files.

    Hand the .visit() method your parse tree from the bvm_grammar to get your list."""

    def generic_visit(self, node, visited_children):
        """Unwrap nodes we don't care about"""
        return visited_children or node

    def visit_label(self, node, children):
        symbol, useless_colon, _ = children

        return Label(symbol.text)

    def visit_filename(self, node, children):
        filename, _ = children

        filename = filename.text
        if filename[0] in ['"', "'"]:
            filename = filename[1:]

        if filename[-1] in ['"', "'"]:
            filename = filename[:-1]

        return Filename(filename)

    def visit_eol(self, node, children):
        return '' #nobody cares about the EOLs

    def visit_line(self, node, children):
        output = []

        for child in flatten(children):
            if type(child) == Node or child == "":
                continue

            output.append(child)

        return output

    def visit_lines(self, node, children):
        output = []

        for child in flatten(children):
            try:
                if child.text.strip() == "":
                    continue
            except AttributeError:
                try:
                    if child.strip() == "":
                        continue
                except AttributeError:
                    pass

            output.append(child)

        return output
