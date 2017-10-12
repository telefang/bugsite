from CodeModule import cmodel

class Bof1Symbol(cmodel.Struct):
    name = cmodel.String("ascii")
    symtype = cmodel.Enum(cmodel.U8, "LOCAL", "IMPORT", "EXPORT")
    value = cmodel.If("symtype", lambda x: x in [0, 2], cmodel.LeU32)
    
    __order__ = ["name", "symtype", "value"]

class Bof1LimitExpr(cmodel.Struct):
    lolimit = cmodel.LeS32
    hilimit = cmodel.LeS32

    __order__ = ["lolimit", "hilimit"]

class Bof1PatchExpr(cmodel.Union):
    __tag__ = cmodel.Enum(cmodel.U8, "ADD", "SUB", "MUL", "DIV", "MOD", "UNSUB", "OR", "AND", "XOR", "UNNOT", "LOGAND", "LOGOR", "LOGUNNOT", "LOGEQ", "LOGNE", "LOGGT", "LOGLT", "LOGGE", "LOGLE", "SHL", "SHR", "BANK", "HRAM", ("CONST", 0x80), ("SYM", 0x81), ("INDIR", 0x82))
    
    RANGECHECK = Bof1LimitExpr
    CONST = cmodel.LeU32
    SYM = cmodel.LeU32
    BANK = cmodel.LeU32
    INDIR = cmodel.LeU32
    
class Bof1Patch(cmodel.Struct):
    srcfile = cmodel.String("ascii")
    srcline = cmodel.LeU32
    patchoffset = cmodel.LeU32
    patchtype = cmodel.Enum(cmodel.U8, "BYTE", "LE16", "LE32", "BE16", "BE32")
    
    numpatchexprs = cmodel.LeU32
    patchexprs = cmodel.Array(Bof1PatchExpr, "numpatchexprs", countType = cmodel.BytesCount)
    
    __order__ = ["srcfile", "srcline", "patchoffset", "patchtype", "numpatchexprs", "patchexprs"]

class Bof1(cmodel.Struct):
    magic = cmodel.Magic(b"BOF1")
    
    #BugVM code lives within separate files, so we don't have sections in the
    #same way that Rgbds object files do. Each bvm object file has one section,
    #and then symbol fixups on that section.
    datasize = cmodel.LeU32
    numsymbols = cmodel.LeU32
    numpatches = cmodel.LeU32
    
    data = cmodel.Blob('datasize')
    symbols = cmodel.Array(Bof1Symbol, "numsymbols")
    patches = cmodel.Array(Bof1Patch, "numpatches")
    
    __order__ = ["magic", "datasize", "numsymbols", "numpatches", "data", "symbols", "patches"]