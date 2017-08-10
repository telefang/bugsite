"""Defines our exception vocabulary for BugTools.

All exceptions are a subclass of a reasonable Python builtin exception type.
You aren't expected to remember these."""

class LocalSymbolError(LookupError):
    """User provided BVM source contains a .local label that could not be
    globalized because there is no parent label to attach it to."""
    def __init__(self, symbol_name):
        self.symbol_name = symbol_name

    def __str__(self):
        return "Local label %s does not have a non-local parent to attach to." % self.symbol_name

class CircularEquateError(LookupError):
    """User provided BVM source contains an equate which forms an unresolvable circular reference."""
    def __init__(self, symbol_names):
        self.symbol_names = symbol_names

    def __str__(self):
        return "The following equates are undefined or defined as an unresolvable circular reference: %s" % repr(self.symbol_names)

class InvalidOperandError(TypeError):
    """User provided operand could not be encoded into specified instruction."""
    def __init__(self, instr):
        self.instr = instr

    def __str__(self):
        return "Operands given for opcode %s are not valid: %s" % (repr(self.instr.opcode), repr(self.instr.operands))

class InvalidOpcodeError(SyntaxError):
    """User provided instruction has invalid opcode or prefix."""
    def __init__(self, instr):
        self.instr = instr

    def __str__(self):
        return "Opcode %s is not a valid or known BugVM opcode." % (repr(self.instr.opcode),)
