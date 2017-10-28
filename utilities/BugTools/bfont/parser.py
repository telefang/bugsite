from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor, Node

from BugTools.util import flatten

bfont_grammar = Grammar(
    """
    lines = _ line*
    line = (width eol) / eol
    width = "width " string ", " decimal
    
    string = (~"[\\\"][^\\\"]*[\\\"]"i _) / (~"[\\'][^\\']*[\\']"i _)
    decimal = ~"[0-9]+" _

    #This production exists entirely to ensure other productions don't try to
    #merge entire newlines together.
    eol = _? newline _?
    newline = ~"[\\r\\n]"

    #These productions pull whitespace and comments out of the parsetree
    _ = meaninglessness*
    meaninglessness = whitespace / comment
    comment = ~";[^\\r\\n]*"
    whitespace = ~"[ \t]+"
    """
)

class FontWidthVisitor(NodeVisitor):
    """Converts a parsed .bfont tree into a font width mapping."""
    
    def generic_visit(self, node, visited_children):
        """Unwrap nodes we don't care about"""
        return visited_children or node

    def visit_string(self, node, children):
        strdata, _ = children[0]
        
        return strdata.text[1:-1].replace('\\"', '"').replace("\\'", "'")

    def visit_decimal(self, node, children):
        decdata, _ = children

        return int(decdata.text, 10);
    
    def visit_width(self, node, children):
        wdecl, target_string, comma, decimal = children
        
        return (target_string, decimal)
    
    def visit_eol(self, node, children):
        return '' #nobody cares about the EOLs

    def visit_line(self, node, children):
        output = []

        for child in flatten(children):
            if type(child) == Node or type(child) == str and child == "":
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