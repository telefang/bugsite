from BugTools.fs.parser import Label, Filename
from BugTools.bvm.object import Bof1, Bof1Patch, Bof1PatchExpr, Bof1Symbol
from CodeModule import cmodel
from CodeModule.asm.rgbds import Rgb4, Rgb4Patch, Rgb4Section, Rgb4Symbol, Rgb4PatchExpr, Rgb4LimitExpr

import os.path

class Directory(cmodel.Struct):
    basebank = cmodel.U8
    baseoffset = cmodel.LeU16
    filesize = cmodel.LeU16
    padding1 = cmodel.U8
    padding2 = cmodel.U8
    padding3 = cmodel.U8

    __order__ = ["basebank", "baseoffset", "filesize", "padding1", "padding2", "padding3"]

def depstring(parselist):
    """Convert a parsed .bfs listing into a depstring for the Makefile."""
    deps = set()

    for command in parselist:
        if type(command) is Filename:
            deps.add(command.path)

    return " ".join(deps)

PATCH_LENGTHS = {Bof1Patch.BYTE: 1, Bof1Patch.LE16: 2, Bof1Patch.LE32: 4, Bof1Patch.BE16: 2, Bof1Patch.BE32: 4}
PATCH_LITTLE_ENDIAN = {Bof1Patch.BYTE: True, Bof1Patch.LE16: True, Bof1Patch.LE32: True, Bof1Patch.BE16: False, Bof1Patch.BE32: False}

def translate_bof1_patchexprs_to_rgb4(bofpatchexprs, symbol_dict):
    rgbpatchexprs = []

    for bofpatchexpr in bofpatchexprs:
        rgbpatchexpr = Rgb4PatchExpr()

        if bofpatchexpr.__tag__ == Bof1PatchExpr.INDIR:
            #INDIR values become (SYM - 0xC400) / 2
            rgbpatchexpr.__tag__ = Rgb4PatchExpr.SYM
            rgbpatchexpr.SYM = symbol_dict[bofpatchexpr.INDIR]

            rgbpatchexprs.append(rgbpatchexpr)

            rgbpatchexpr = Rgb4PatchExpr()
            rgbpatchexpr.__tag__ = Rgb4PatchExpr.CONST
            rgbpatchexpr.CONST = 0xC400

            rgbpatchexprs.append(rgbpatchexpr)

            rgbpatchexpr = Rgb4PatchExpr()
            rgbpatchexpr.__tag__ = Rgb4PatchExpr.SUB

            rgbpatchexprs.append(rgbpatchexpr)

            rgbpatchexpr = Rgb4PatchExpr()
            rgbpatchexpr.__tag__ = Rgb4PatchExpr.CONST
            rgbpatchexpr.CONST = 0x2

            rgbpatchexprs.append(rgbpatchexpr)

            rgbpatchexpr = Rgb4PatchExpr()
            rgbpatchexpr.__tag__ = Rgb4PatchExpr.DIV

            rgbpatchexprs.append(rgbpatchexpr)
        elif bospatchexpr.__tag__ == Bof1PatchExpr.RANGECHECK:
            rgbpatchexpr.__tag__ = bofpatchexpr.__tag__
            rgbpatchexpr.RANGECHECK = Rgb4LimitExpr()
            rgbpatchexpr.RANGECHECK.lolimit = bofpatchexpr.RANGECHECK.lolimit
            rgbpatchexpr.RANGECHECK.hilimit = bofpatchexpr.RANGECHECK.hilimit
        elif bofpatchexpr.__tag__ == Bof1PatchExpr.CONST:
            rgbpatchexpr.__tag__ = bofpatchexpr.__tag__
            rgbpatchexpr.CONST = bofpatchexpr.CONST
        elif bofpatchexpr.__tag__ == Bof1PatchExpr.SYM:
            rgbpatchexpr.__tag__ = bofpatchexpr.__tag__
            rgbpatchexpr.SYM = symbol_dict[bofpatchexpr.SYM]
        elif bofpatchexpr.__tag__ == Bof1PatchExpr.BANK:
            rgbpatchexpr.__tag__ = bofpatchexpr.__tag__
            rgbpatchexpr.BANK = symbol_dict[bofpatchexpr.BANK]
        else:
            #All others are translated normally
            rgbpatchexpr.__tag__ = bofpatchexpr.__tag__

    return rgbpatchexprs

def translate_bof1_fixups_to_rgb4(bofpatches, symbol_dict, startoff, endoff):
    """Given a list of bof1 fixups, translate patches to rgb4 format.

    The given startoff and endoff values determine which patches will be
    translated. Patches which straddle this boundary will be truncated as
    appropriate.

    symbol_dict is the mapping between the symbol IDs of the Bof1 file you are
    reading and the Rgb4 file you are making. It must encompass all of the
    symbols mentioned in these patches."""

    rgbpatches = []

    #Translate any fixups to rgbds format
    for bofpatch in bofpatches:
        patchlen = PATCH_LENGTHS[bofpatch.patchtype]

        if bofpatch.patchoffset < startoff + patchlen - 1 or bofpatch.patchoffset > endoff:
            continue

        patch_cut_start = startoff - bofpatch.patchoffset
        patch_cut_end = patchlen - endoff - bofpatch.patchoffset
        patch_is_le = PATCH_LITTLE_ENDIAN[bofpatch.patchtype]

        if patch_cut_start > 0 or patch_cut_end > 0:
            #HARD PATH: make a patch for each byte of the original.
            for byte_i in range(0, patchlen):
                if patch_cut_start < byte_i:
                    continue

                if (patchlen - byte_i) < patch_cut_end:
                    continue

                if patch_is_le:
                    shift_i = byte_i
                else:
                    shift_i = patchlen - 1 - shift_i

                #Create a new patch for this byte only.
                rgbpatch = Rgb4Patch()
                rgbpatch.srcfile = bofpatch.srcfile
                rgbpatch.srcline = bofpatch.srcline
                rgbpatch.patchoffset = bofpatch.patchoffset - startoff + byte_i
                rgbpatch.patchtype = Rgb4Patch.BYTE
                rgbpatch.patchexprs = translate_bof1_patchexprs_to_rgb4(bofpatch.patchexprs, symbol_dict)

                #Equivalent to (patchexpr) >> (shift_i * 8) & 0xFF
                #Due to the way RPN works this should also work if the translate
                #function also applied it's INDIR change
                rgbpatchexpr = Rgb4PatchExpr()
                rgbpatchexpr.__tag__ = Rgb4PatchExpr.CONST
                rgbpatchexpr.CONST = shift_i * 8

                rgbpatch.patchexprs.append(rgbpatchexpr)

                rgbpatchexpr = Rgb4PatchExpr()
                rgbpatchexpr.__tag__ = Rgb4PatchExpr.SHR

                rgbpatch.patchexprs.append(rgbpatchexpr)

                rgbpatchexpr = Rgb4PatchExpr()
                rgbpatchexpr.__tag__ = Rgb4PatchExpr.CONST
                rgbpatchexpr.CONST = 0xFF

                rgbpatch.patchexprs.append(rgbpatchexpr)

                rgbpatchexpr = Rgb4PatchExpr()
                rgbpatchexpr.__tag__ = Rgb4PatchExpr.AND

                rgbpatch.patchexprs.append(rgbpatchexpr)

                rgbpatches.append(rgbpatch)
        else:
            #EASY PATH: Just copy everything over.
            rgbpatch = Rgb4Patch()
            rgbpatch.srcfile = bofpatch.srcfile
            rgbpatch.srcline = bofpatch.srcline
            rgbpatch.patchoffset = bofpatch.patchoffset - startoff
            rgbpatch.patchtype = bofpatch.patchtype
            rgbpatch.patchexprs = translate_bof1_patchexprs_to_rgb4(bofpatch.patchexprs, symbol_dict)

            rgbpatches.append(rgbpatch)

    return rgbpatches

def fsimage(parselist, basedir, dirbank = 0xA, databank = 0xC):
    """Construct a series of RGBDS sections corresponding to our filesystem.

    dirbank is the index of the directory structure bank. Directory data will be
    added to this bank according to the BugFS directory structure, for as many
    banks as needed.

    databank is the index of the first data bank. Data from each file will be
    densely packed into each bank. Files will be spanned across bank boundaries
    if needed. The databank index must be greater than the last directory bank
    in use.

    The returned Rgb4 object file will contain sections with the filesystem
    data. One symbol will be exposed for the directory.

    If any Bof1 object files are present in the filesystem directory, their
    respective fixups and symbol exports will be bridged into the resulting
    RGBDS image."""

    #Filter out the parselist. We only care about file references.
    filepaths = []

    for command in parselist:
        if type(command) is Filename:
            filepaths.append(command.path)

    #Collect all the data into a single array, we'll chop it up later.
    datum = []

    #Construct a directory listing for everything.
    directory = []
    start_bank = databank
    start_offset = 0x0000

    datum_section = Rgb4Section()
    datum_section.name = "BugFS Data %s" % start_bank
    datum_section.sectype = Rgb4Section.ROMX
    datum_section.org = 0x4000
    datum_section.bank = start_bank
    datum_data = []

    #Also we're going to be building the Rgb4 object at the same time...
    rgb4obj = Rgb4()
    rgb4_syms = {}

    for path in filepaths:
        new_dir = Directory()
        new_dir.basebank = start_bank
        new_dir.baseoffset = start_offset

        bvmdata = Bof1()

        with open(os.path.join(basedir, path), 'rb') as file:
            if path.endswith(".bof"):
                #This is a BVM Object File, bridge it into the RGBDS section...
                bvmdata.load(file)
                new_dir.filesize = len(bvmdata.data)
            else:
                #This is raw data, repack it as a BOF for now
                bindata = file.read()
                new_dir.filesize = len(bindata)

                bvmdata.data = bindata

        directory.append(new_dir.bytes)

        #Map bvmdata symbols into rgb4obj
        bvm_to_rgb4 = {}
        for bofsymid, bofsym in enumerate(bvmdata.symbols):
            if bofsym.name not in rgb4_syms.keys():
                symid = len(rgb4obj.symbols)
                rgbsym = Rgb4Symbol()

                #TODO: Should we translate symbol values to native?
                rgbsym.name = bofsym.name
                rgbsym.symtype = bofsym.symtype
                if bofsym.symtype in [Bof1Symbol.LOCAL, Bof1Symbol.EXPORT]:
                    rgbsym.value = bofsym.value

                rgb4obj.symbols.append(rgbsym)
                rgb4_syms[rgbsym.name] = symid

            bvm_to_rgb4[bofsymid] = rgb4_syms[bofsym.name]

        #At this point we need to separate the BOF data into bank-sized chunks
        #so that RGBDS can deal with it.
        written_chunk_size = 0
        chunk_local_offset = start_offset

        while written_chunk_size < len(bvmdata.data):
            cur_chunk_size = min((0x4000 - chunk_local_offset), len(bvmdata.data) - written_chunk_size)
            cur_chunk = bvmdata.data[written_chunk_size:written_chunk_size + cur_chunk_size]

            datum_data.append(cur_chunk)
            datum_section.datsec.patches = datum_section.datsec.patches + translate_bof1_fixups_to_rgb4(bvmdata.patches, bvm_to_rgb4, written_chunk_size, written_chunk_size + cur_chunk_size)

            written_chunk_size += cur_chunk_size
            start_offset += cur_chunk_size
            if start_offset >= 0x4000:
                start_offset -= 0x4000
                start_bank += 1

                datum_section.data = b"".join(datum_data)
                rgb4obj.sections.append(datum_section)

                datum_section = Rgb4Section()
                datum_section.name = "BugFS Data %s" % start_bank
                datum_section.sectype = Rgb4Section.ROMX
                datum_section.org = 0x4000
                datum_section.bank = start_bank
                datum_data = []

    #Flush the final data section's contents...
    if len(datum_data) > 0:
        datum_section.data = b"".join(datum_data)
        rgb4obj.sections.append(datum_section)

    #Build the BFS directory structure
    directory = b"".join(directory)
    start_bank = dirbank

    while len(directory) > 0:
        directory_section = Rgb4Section()
        directory_section.name = "BugFS Directory %s" % start_bank
        directory_section.sectype = Rgb4Section.ROMX
        directory_section.org = 0x4000
        directory_section.bank = start_bank
        directory_section.datsec.data = directory[:0x4000]

        rgb4obj.sections.append(directory_section)

        directory = directory[0x4000:]
        start_bank += 1

    directory_symbol = Rgb4Symbol()
    directory_symbol.name = "BugFS_Directory"
    directory_symbol.symtype = Rgb4Symbol.EXPORT
    directory_symbol.value.sectionid = 0 #Index of what section this symbol is in
    directory_symbol.value.value = 0 #Offset from the start of said section

    rgb4obj.symbols.append(directory_symbol)

    return rgb4obj
