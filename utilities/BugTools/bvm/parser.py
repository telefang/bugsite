from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor, Node

from BugTools.util import flatten

bvm_grammar = Grammar(
    """
    lines = _ line*
    line = (equate eol) / (instruction eol) / (label? instruction? eol) / (comment eol) / eol
    equate = symbol _ "EQU" _ (literali / symbol) comment?
    instruction = (opcode operand* comment?) / (opcode comment?)
    operand = (literali / symbol) list_separator?
    literali = string / hex / decimal #can't be named literal or we can't visit it

    #These productions define what our data types look like.
    #We are not encoding the actual set of valid opcodes in the production
    #table so we can flag a different error message for that kind of syntax.
    #Okay we do encode NPREF because it's a butt
    string = ~"[\'\\"][^\'\\"]*[\'\\"]"i _
    decimal = ~"[0-9]+" _
    hex = "$" ~"[A-F0-9]+"i _
    label = symbol ":"? ":"? comment? _
    symbol = ~"\.?[a-zA-Z_][a-zA-Z_0-9]*"
    opcode = ("NPREF" whitespace)? ~"[a-zA-Z_]+" whitespace*
    list_separator = "," _
    comment = _? ~";[^\\r\\n]*"

    #This production exists entirely to ensure other productions don't try to
    #merge entire newlines together.
    eol = _? newline _?
    newline = ~"[\\r\\n]"

    #These productions pull whitespace out of the parsetree
    _ = meaninglessness*
    meaninglessness = whitespace
    whitespace = ~"[ \t]+"
    """);

class SymbolicRef(object):
    def __init__(self, name, is_local):
        self.name = name
        self.is_local = is_local

    def __repr__(self):
        return "SymbolicRef(%s, %s)" % (repr(self.name), repr(self.is_local))

class Label(object):
    def __init__(self, symbol, is_exported, comment = None):
        self.symbol = symbol
        self.is_exported = is_exported
        self.comment = comment

    def __repr__(self):
        return "Label(%s, %s, %s)" % (repr(self.symbol), repr(self.is_exported), repr(self.comment))

class Instruction(object):
    def __init__(self, opcode, operands, prefix, comment = None):
        self.opcode = opcode.upper()
        self.operands = operands
        self.prefix = prefix
        self.comment = comment

    def __repr__(self):
        return "Instruction(%s, %s, %s, %s)" % (repr(self.opcode), repr(self.operands), repr(self.prefix), repr(self.comment))

class Equate(object):
    def __init__(self, symbol, value_expr, comment = None):
        self.symbol = symbol
        self.value_expr = value_expr
        self.comment = comment

    def __repr__(self):
        return "Equate(%s, %s, %s)" % (repr(self.symbol), repr(self.value_expr), repr(self.comment))

class Comment(object):
    def __init__(self, comment_text):
        self.comment_text = comment_text

    def __repr__(self):
        return "Comment(%s)" % (repr(self.comment_text))

class InstrListVisitor(NodeVisitor):
    """Converts a parsed .bvm tree into a list of labels and instructions.

    Hand the .visit() method your parse tree from the bvm_grammar to get your list."""

    def generic_visit(self, node, visited_children):
        """Unwrap nodes we don't care about"""
        return visited_children or node

    def visit_string(self, node, children):
        strdata, _ = children

        return strdata.text

    def visit_decimal(self, node, children):
        decdata, _ = children

        return int(decdata.text, 10);

    def visit_hex(self, node, children):
        indicator, hexdata, _ = children

        return int(hexdata.text, 16);

    def visit_literali(self, node, children):
        return children[0]

    def visit_symbol(self, node, children):
        return SymbolicRef(node.text, node.text[0] == ".")

    def visit_label(self, node, children):
        symbol, useless_colon, is_exported, comment, _ = children

        try:
            is_exported = is_exported[0]
        except TypeError:
            pass

        is_exported = is_exported.text == ":"

        if type(comment) is Node:
            return Label(symbol, is_exported)
        else:
            return Label(symbol, is_exported, comment[0])

    def visit_opcode(self, node, children):
        prefix, opcode, _ = children

        try:
            prefix = prefix[0]
            prefix, _ = prefix
        except TypeError:
            pass

        return [prefix.text, opcode.text]

    def visit_operand(self, node, children):
        children, _ = children
        value, = children

        return value

    def visit_instruction(self, node, children):
        opcode, operands, comment = children[0]

        try:
            if operands.text == "":
                operands = []
            else:
                operands = [operands.text]
        except AttributeError:
            pass

        if type(comment) is Node:
            return Instruction(opcode[1], operands, opcode[0])
        else:
            return Instruction(opcode[1], operands, opcode[0], comment[0])

    def visit_equate(self, node, children):
        symbol, _, equ, _, value_expr, comment = children

        if type(comment) is Node:
            return Equate(symbol, value_expr[0])
        else:
            return Equate(symbol, value_expr[0], comment[0])

    def visit_comment(self, node, children):
        return Comment("".join(node.text.split(";")[1:]))

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
