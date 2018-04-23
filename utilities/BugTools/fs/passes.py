from BugTools.fs.parser import Label, Filename
from BugTools.bvm.object import Bof1, Bof1Patch, Bof1PatchExpr, Bof1Symbol
from CodeModule import cmodel
from CodeModule.asm.rgbds import Rgb6, Rgb6Patch, Rgb6Section, Rgb6Symbol, Rgb6PatchExpr, Rgb6LimitExpr

import os.path

class Directory(cmodel.Struct):
    basebank = cmodel.U8
    baseoffset = cmodel.LeU16
    filesize = cmodel.LeU16
    padding1 = cmodel.U8
    padding2 = cmodel.U8
    padding3 = cmodel.U8

    __order__ = ["basebank", "baseoffset", "filesize", "padding1", "padding2", "padding3"]

def depstring(parselist, basedir):
    """Convert a parsed .bfs listing into a depstring for the Makefile.

    basedir is the directory to look for files in. It may be a single string or
    a list. Paths mentioned within parselist may reside in any of the listed
    directories. If a file is not present in any of those directories, we will
    append the first basedir in the list. Basedir may be a single string if only
    one directory is to be used."""
    deps = set()

    #If only one basedir is provided, list it up anyway
    if type(basedir) is not list:
        basedir = [basedir]

    for command in parselist:
        if type(command) is Filename:
            for base in basedir:
                try:
                    with open(base + "/" + command.path, 'rb') as file:
                        deps.add(base + "/" + command.path)
                        break
                except FileNotFoundError:
                    continue
            else:
                #File missing, which means it needs to be built in the build dir
                deps.add(basedir[0] + "/" + command.path)

    return " ".join(deps)

PATCH_LENGTHS = {Bof1Patch.BYTE: 1, Bof1Patch.LE16: 2, Bof1Patch.LE32: 4, Bof1Patch.BE16: 2, Bof1Patch.BE32: 4}
PATCH_LITTLE_ENDIAN = {Bof1Patch.BYTE: True, Bof1Patch.LE16: True, Bof1Patch.LE32: True, Bof1Patch.BE16: False, Bof1Patch.BE32: False}

def translate_bof1_patchexprs_to_rgb6(bofpatchexprs, symbol_dict):
    rgbpatchexprs = []
    
    for bofpatchexpr in bofpatchexprs:
        rgbpatchexpr = Rgb6PatchExpr()

        if bofpatchexpr.__tag__ == Bof1PatchExpr.INDIR:
            #INDIR values become (SYM - 0xC400) / 2
            rgbpatchexpr.__tag__ = Rgb6PatchExpr.SYM
            rgbpatchexpr.SYM = symbol_dict[bofpatchexpr.INDIR]
            
            rgbpatchexprs.append(rgbpatchexpr)
            
            rgbpatchexpr = Rgb6PatchExpr()
            rgbpatchexpr.__tag__ = Rgb6PatchExpr.CONST
            rgbpatchexpr.CONST = 0xC400
            
            rgbpatchexprs.append(rgbpatchexpr)
            
            rgbpatchexpr = Rgb6PatchExpr()
            rgbpatchexpr.__tag__ = Rgb6PatchExpr.SUB
            
            rgbpatchexprs.append(rgbpatchexpr)
            
            rgbpatchexpr = Rgb6PatchExpr()
            rgbpatchexpr.__tag__ = Rgb6PatchExpr.CONST
            rgbpatchexpr.CONST = 0x2
            
            rgbpatchexprs.append(rgbpatchexpr)
            
            rgbpatchexpr = Rgb6PatchExpr()
            rgbpatchexpr.__tag__ = Rgb6PatchExpr.DIV
            
            rgbpatchexprs.append(rgbpatchexpr)
        elif bospatchexpr.__tag__ == Bof1PatchExpr.RANGECHECK:
            rgbpatchexpr.__tag__ = bofpatchexpr.__tag__
            rgbpatchexpr.RANGECHECK = Rgb6LimitExpr()
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

def translate_bof1_fixups_to_rgb6(bofpatches, symbol_dict, startoff, endoff, patchoffset):
    """Given a list of bof1 fixups, translate patches to rgb6 format.
    
    The given startoff and endoff values determine which patches will be
    translated. Patches which straddle this boundary will be truncated as
    appropriate. patchoffset is how many bytes patches should be offset in the
    resulting section.
    
    symbol_dict is the mapping between the symbol IDs of the Bof1 file you are
    reading and the Rgb6 file you are making. It must encompass all of the
    symbols mentioned in these patches."""
    
    rgbpatches = []
    
    #Translate any fixups to rgbds format
    for bofpatch in bofpatches:
        patchlen = PATCH_LENGTHS[bofpatch.patchtype]
        
        if bofpatch.patchoffset < startoff - patchlen + 1 or bofpatch.patchoffset > endoff:
            continue
            
        patch_cut_start = startoff - bofpatch.patchoffset
        patch_cut_end = patchlen - endoff - bofpatch.patchoffset
        patch_is_le = PATCH_LITTLE_ENDIAN[bofpatch.patchtype]
        
        if patch_cut_start > 0 or patch_cut_end > 0 or True:
            #HARD PATH: make a patch for each byte of the original.
            for byte_i in range(0, patchlen):
                if patch_cut_start > byte_i:
                    continue
                
                if (patchlen - byte_i) < patch_cut_end:
                    continue
                
                if patch_is_le:
                    shift_i = byte_i
                else:
                    shift_i = patchlen - 1 - shift_i
                
                #Create a new patch for this byte only.
                rgbpatch = Rgb6Patch()
                rgbpatch.srcfile = bofpatch.srcfile
                rgbpatch.srcline = bofpatch.srcline
                rgbpatch.patchoffset = bofpatch.patchoffset - startoff + byte_i + patchoffset
                rgbpatch.patchtype = Rgb6Patch.BYTE
                rgbpatch.patchexprs = translate_bof1_patchexprs_to_rgb6(bofpatch.patchexprs, symbol_dict)
                
                #Equivalent to (patchexpr) >> (shift_i * 8) & 0xFF
                #Due to the way RPN works this should also work if the translate
                #function also applied it's INDIR change
                rgbpatchexpr = Rgb6PatchExpr()
                rgbpatchexpr.__tag__ = Rgb6PatchExpr.CONST
                rgbpatchexpr.CONST = shift_i * 8
                
                rgbpatch.patchexprs.append(rgbpatchexpr)
                
                rgbpatchexpr = Rgb6PatchExpr()
                rgbpatchexpr.__tag__ = Rgb6PatchExpr.SHR
                
                rgbpatch.patchexprs.append(rgbpatchexpr)
                
                rgbpatchexpr = Rgb6PatchExpr()
                rgbpatchexpr.__tag__ = Rgb6PatchExpr.CONST
                rgbpatchexpr.CONST = 0xFF
                
                rgbpatch.patchexprs.append(rgbpatchexpr)
                
                rgbpatchexpr = Rgb6PatchExpr()
                rgbpatchexpr.__tag__ = Rgb6PatchExpr.AND
                
                rgbpatch.patchexprs.append(rgbpatchexpr)
                
                rgbpatches.append(rgbpatch)
        else:
            #EASY PATH: Just copy everything over.
            rgbpatch = Rgb6Patch()
            rgbpatch.srcfile = bofpatch.srcfile
            rgbpatch.srcline = bofpatch.srcline
            rgbpatch.patchoffset = bofpatch.patchoffset - startoff + patchoffset
            rgbpatch.patchtype = bofpatch.patchtype
            rgbpatch.patchexprs = translate_bof1_patchexprs_to_rgb6(bofpatch.patchexprs, symbol_dict)
            
            rgbpatches.append(rgbpatch)
    
    return rgbpatches

def fsimage(parselist, basedir, dirbank = 0xA, databank = 0xC):
    """Construct a series of RGBDS sections corresponding to our filesystem.

    basedir is the directory to look for files in. It may be a single string or
    a list. Paths mentioned within parselist may reside in any of the listed
    directories.

    dirbank is the index of the directory structure bank. Directory data will be
    added to this bank according to the BugFS directory structure, for as many
    banks as needed.

    databank is the index of the first data bank. Data from each file will be
    densely packed into each bank. Files will be spanned across bank boundaries
    if needed. The databank index must be greater than the last directory bank
    in use.

    The returned Rgb6 object file will contain sections with the filesystem
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
    
    datum_section = Rgb6Section()
    datum_section.name = "BugFS Data %s" % start_bank
    datum_section.sectype = Rgb6Section.ROMX
    datum_section.org = 0x4000
    datum_section.bank = start_bank
    datum_data = []
    
    #Also we're going to be building the Rgb6 object at the same time...
    rgb6obj = Rgb6()
    rgb6_syms = {}

    #If only one basedir is provided, list it up anyway
    if type(basedir) is not list:
        basedir = [basedir]

    for path in filepaths:
        new_dir = Directory()
        new_dir.basebank = start_bank
        new_dir.baseoffset = start_offset
        
        bvmdata = Bof1()
        
        for base in basedir:
            try:
                with open(os.path.join(base, path), 'rb') as file:
                    if path.endswith(".bof"):
                        #This is a BVM Object File, bridge it into the RGBDS section...
                        bvmdata.load(file)
                        new_dir.filesize = len(bvmdata.data)
                    else:
                        #This is raw data, repack it as a BOF for now
                        bindata = file.read()
                        new_dir.filesize = len(bindata)

                        bvmdata.data = bindata

                    break
            except FileNotFoundError:
                continue
        else:
            raise FileNotFoundError(path)
        
        directory.append(new_dir.bytes)
        
        #Map bvmdata symbols into rgb6obj
        bvm_to_rgb6 = {}
        for bofsymid, bofsym in enumerate(bvmdata.symbols):
            if bofsym.name not in rgb6_syms.keys():
                symid = len(rgb6obj.symbols)
                rgbsym = Rgb6Symbol()
                
                #TODO: Should we translate symbol values to native?
                rgbsym.name = bofsym.name
                rgbsym.symtype = bofsym.symtype
                if bofsym.symtype in [Bof1Symbol.LOCAL, Bof1Symbol.EXPORT]:
                    rgbsym.value = bofsym.value
                
                rgb6obj.symbols.append(rgbsym)
                rgb6_syms[rgbsym.name] = symid
            
            bvm_to_rgb6[bofsymid] = rgb6_syms[bofsym.name]
        
        #At this point we need to separate the BOF data into bank-sized chunks
        #so that RGBDS can deal with it.
        written_chunk_size = 0
        chunk_local_offset = start_offset
        
        while written_chunk_size < len(bvmdata.data):
            cur_chunk_size = min((0x4000 - start_offset), len(bvmdata.data) - written_chunk_size)
            cur_chunk = bvmdata.data[written_chunk_size:(written_chunk_size + cur_chunk_size)]

            if type(cur_chunk_size) is not int:
                raise Exception("Assertion failed: Chunk size is invalid")

            if cur_chunk_size > 0x4000:
                raise Exception("Assertion failed: Chunk size is invalid")

            if cur_chunk_size != len(cur_chunk):
                raise Exception("Assertion failed: Chunk size is invalid")
            
            datum_data.append(cur_chunk)
            datum_section.datsec.patches.extend(translate_bof1_fixups_to_rgb6(bvmdata.patches, bvm_to_rgb6, written_chunk_size, written_chunk_size + cur_chunk_size, start_offset))
            
            written_chunk_size += cur_chunk_size
            start_offset += cur_chunk_size
            if start_offset >= 0x4000:
                start_offset -= 0x4000
                start_bank += 1
                
                datum_section.datsec.data = b"".join(datum_data)
                rgb6obj.sections.append(datum_section)
                
                datum_section = Rgb6Section()
                datum_section.name = "BugFS Data %s" % start_bank
                datum_section.sectype = Rgb6Section.ROMX
                datum_section.org = 0x4000
                datum_section.bank = start_bank
                datum_data = []
    
    #Flush the final data section's contents...
    if len(datum_data) > 0:
        datum_section.datsec.data = b"".join(datum_data)
        rgb6obj.sections.append(datum_section)

    #Build the BFS directory structure
    directory = b"".join(directory)
    start_bank = dirbank

    while len(directory) > 0:
        if start_bank == dirbank:
            directory_symbol = Rgb6Symbol()
            directory_symbol.name = "BugFS_Directory"
            directory_symbol.symtype = Rgb6Symbol.EXPORT
            directory_symbol.value.sectionid = len(rgb6obj.sections)
            directory_symbol.value.value = 0

            rgb6obj.symbols.append(directory_symbol)

        directory_section = Rgb6Section()
        directory_section.name = "BugFS Directory %s" % start_bank
        directory_section.sectype = Rgb6Section.ROMX
        directory_section.org = 0x4000
        directory_section.bank = start_bank
        directory_section.datsec.data = directory[:0x4000]

        rgb6obj.sections.append(directory_section)

        directory = directory[0x4000:]
        start_bank += 1

    return rgb6obj
