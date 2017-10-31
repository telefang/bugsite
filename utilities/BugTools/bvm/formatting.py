from BugTools.bvm.parser import Equate, SymbolicRef, Label, Instruction, Comment
from BugTools.exceptions import InvalidOperandError

def unparse_bvm(parselist, strdec = None):
    """Given a parsed BVM, emit a source code representation of the data.
    
    This can be used to conform existing BVM source code to new formatting
    standards, perform automated rewrites of existing BVM source, or debug the
    output of a particularly problematic compilation pass.
    
    A string decoder is needed because certain internal assembler passes will
    translate a string value into a byte value. It may be safely ommitted only
    if the parselist does not contain instructions with byte 
    
    Returns a string with BVM source code inside."""
    
    source = []
    
    last_line_tabbed = False

    for instr in parselist:
        if type(instr) is Equate:
            if instr.symbol.is_local:
                source.append(".")
            
            source.append(instr.symbol.name + " EQU ")
            
            if type(instr.value_expr) is int:
                source.append("$%X" % instr.value_expr)
            elif type(instr.value_expr) is str:
                source.append('"%s"' % instr.value_expr)
            elif type(instr.value_expr) is bytes:
                source.append('"%s"' % strdec(instr.value_expr))
            elif type(instr.value_expr) is SymbolicRef:
                if instr.value_expr.is_local:
                    source.append("." + instr.value_expr.name)
                else:
                    source.append(instr.value_expr.name)
            else:
                raise SyntaxError()
            
            if instr.comment is not None:
                source.append(" ;")
                source.append(instr.comment.comment_text)

            source.append("\n")

            last_line_tabbed = False
        elif type(instr) is Label:
            source.append("\n")
            
            source.append(instr.symbol.name)
            
            if instr.is_exported:
                source.append("::")
            elif not instr.symbol.is_local:
                source.append(":")
            
            if instr.comment is not None:
                source.append(" ;")
                source.append(instr.comment.comment_text)

            source.append("\n")

            last_line_tabbed = False
        elif type(instr) is Instruction:
            #We follow PEP303 in our assembly, treating each instruction as
            #"nested" inside a "block" formed by the assembler label.
            source.append("    ")
            
            if instr.prefix not in [None, ""]:
                source.append(instr.prefix)
                source.append(" ")
            
            source.append(instr.opcode)
            source.append(" ")
            
            operand_str = []
            for operand in instr.operands:
                if type(operand) is int:
                    source.append("$%X" % operand)
                elif type(operand) is str:
                    source.append('"%s"' % operand)
                elif type(operand) is bytes:
                    source.append('"%s"' % strdec(operand))
                elif type(operand) is SymbolicRef:
                    source.append(operand.name)
                else:
                    raise SyntaxError()
            
            source.append(", ".join(operand_str))

            if instr.comment is not None:
                source.append(" ;")
                source.append(instr.comment.comment_text)

            source.append("\n")

            last_line_tabbed = True
        elif type(instr) is Comment:
            #Bare comments are printed on the same level as their contents.
            if last_line_tabbed:
                source.append("    ")

            source.append(";")
            source.append(instr.comment_text)
            source.append("\n")
    return "".join(source)
