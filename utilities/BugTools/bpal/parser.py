from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor, Node

from BugTools.util import flatten

bpal_grammar = Grammar(
    """
    lines = _ line*
    line = (palette eol) / (label? palette? eol) / eol
    palette = color color color color _
    color = ~"#" hexit hexit hexit ~","? _

    label = ~"[a-zA-Z_][a-zA-Z_0-9]*" ":" _
    hexit = ~"[A-F0-9]"i ~"[A-F0-9]"i

    eol = _? newline _?
    newline = ~"[\\r\\n]"

    _ = meaninglessness*
    meaninglessness = whitespace / comment
    comment = ~";[^\\r\\n]*"
    whitespace = ~"[ \t]+"
    """
)

class Label(object):
    def __init__(self, symbol):
        self.symbol = symbol

    def __repr__(self):
        return "Label(%s)" % (repr(self.symbol),)

class PaletteEntry(object):
    def __init__(self, colors):
        self.colors = colors

    def __repr__(self):
        return "PaletteEntry(%s)" % (repr(self.colors), )

class Color(object):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return "Color(%s, %s, %s)" % (repr(self.r), repr(self.g), repr(self.b))

class PaletteDataVisitor(NodeVisitor):
    """Convert a parsed .bpal syntax tree into a list of palettes."""

    def generic_visit(self, node, children):
        """Unwrap nodes we don't care about"""
        return children or node

    def visit_hexit(self, node, children):
        idat = 0

        for child in children:
            idat = (idat << 4) + int(child.text, 16)

        return idat

    def visit_color(self, node, children):
        return Color(children[1], children[2], children[3])

    def visit_palette(self, node, children):
        return PaletteEntry([children[0], children[1], children[2], children[3]])

    def visit_label(self, node, children):
        symbol, useless_colon, _ = children

        return Label(symbol.text)

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
