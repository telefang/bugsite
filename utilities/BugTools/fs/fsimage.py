import io
import itertools
import sys
import os

from BugTools.fs.structs import Directory
from BugTools.fs.parser import Filename
from BugTools.bvm.object import Bof1, Bof1Symbol, Bof1Patch, Bof1PatchExpr

def print_binary_data_as_source(bytestr, file=None):
    """Prints binary data such that RGBDS will assemble it as such.
    
    e.g. given "\x00\xAB\x1F" it will print
    
        db $00, $AB, $1F
    
    Care is taken to avoid creating overly long lines by printing a newline
    every 16 bytes."""
    
    for line in itertools.batched(bytestr, 16):
        bytes_written = []

        for byte in line:
            # For some reason we get called with lists or bytestrings,
            # and we need the iteration to give us ints.
            # If we don't get ints, demand them anyway
            if isinstance(byte, bytes):
                byte = byte[0]
            
            bytes_written.append(f"${byte:02x}")
        
        bytes_list = ", ".join(bytes_written)
        print(f"    db {bytes_list}", file=file)

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

    The returned RGBDS assembler source will contain sections with the
    filesystem data. One symbol will be exposed for the directory.
    
    If any Bof1 object files are present in the filesystem directory, their
    respective fixups and symbol exports will be translated back into ASM
    source. All other files will be INCBIN'd."""

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

    with io.StringIO() as datum_section:
        print(f"SECTION \"BugFS Data {start_bank}\", ROMX[$4000], BANK[{start_bank}]", file=datum_section)
        
        rgb6_syms = {}

        #If only one basedir is provided, list it up anyway
        if type(basedir) is not list:
            basedir = [basedir]
        
        # First, build up our directory.
        # We need to know the output file sizes of everything here,
        # and everything can spill into multiple banks. So ALMOST EVERYTHING
        # is emitted as `db`s from already-serialized structs.
        for path in filepaths:
            new_dir = Directory()
            new_dir.basebank = start_bank
            new_dir.baseoffset = start_offset
            
            bvmdata = Bof1()
            
            for base in basedir:
                try:
                    with open(os.path.join(base, path), 'rb') as file:
                        if path.endswith(".bof"):
                            bvmdata.load(file)
                            new_dir.filesize = len(bvmdata.data)
                        else:
                            #Raw bytes can be trivially repacked into BOF, so we do so.
                            bindata = file.read()
                            new_dir.filesize = len(bindata)

                            bvmdata.data = bindata

                        break
                except FileNotFoundError:
                    continue
            else:
                raise FileNotFoundError(path)
            
            directory.append(new_dir.bytes)

            imports = {}
            
            for (bofsymid, bofsym) in enumerate(bvmdata.symbols):
                # Bof1 locals and exports are never really used.
                # The directory system makes them basically useless.
                if bofsym.symtype in [Bof1Symbol.LOCAL, Bof1Symbol.EXPORT]:
                    print(f"Ignoring symbol export {bofsym.name}", file=sys.stderr)
                    continue
                
                imports[bofsymid] = bofsym.name

            fixups = [] #tuple of (section offset, symbol name)
            for bofpatch in bvmdata.patches:
                # Continuing the theme here, I checked the other compilers and
                # the only fixups that get emitted are symbol references/INDIR
                # so that's all I implemented.

                if bofpatch.patchtype != Bof1Patch.LE16:
                    print(f"Ignoring unimplemented patch type {bofpatch.patchtype}", file=sys.stderr)
                    continue

                for patchexpr in bofpatch.patchexprs:
                    if patchexpr.__tag__ != Bof1PatchExpr.INDIR:
                        print(f"Ignoring unimplemented fixup type {patchexpr.__tag__}", file=sys.stderr)
                        continue

                    fixups.append((bofpatch.patchoffset, imports[patchexpr.INDIR]))
                    break
            
            fixups.sort(key=lambda t: t[0])

            #At this point we need to separate the BOF data into bank-sized chunks
            #so that RGBDS can deal with it.
            written_chunk_size = 0
            chunk_local_offset = start_offset
            still_need_to_print_high_byte = False
            
            while written_chunk_size < len(bvmdata.data):
                cur_chunk_size = min((0x4000 - start_offset), len(bvmdata.data) - written_chunk_size)
                if type(cur_chunk_size) is not int:
                    raise Exception("Assertion failed: Chunk size is invalid")

                if cur_chunk_size > 0x4000:
                    raise Exception("Assertion failed: Chunk size is invalid")
                
                # There are only two modes for printing chunks out: data or
                # patches. Since we sorted the patch list out, we can just
                # use it as a guide for when to grab data vs. print a symbol
                # reference.
                # 
                # We shrink the current chunk if we have >0 bytes before the
                # next symbol, otherwise we print the symbol without chunking.
                if len(fixups) == 0 or written_chunk_size < fixups[0][0]:
                    if len(fixups) > 0:
                        to_next_fixup = fixups[0][0] - written_chunk_size
                        cur_chunk_size = min(cur_chunk_size, to_next_fixup)
                    
                    cur_chunk = bvmdata.data[written_chunk_size:(written_chunk_size + cur_chunk_size)]
                    if cur_chunk_size != len(cur_chunk):
                        raise Exception("Assertion failed: Chunk size is invalid")
                    
                    print_binary_data_as_source(cur_chunk, file=datum_section)
                else:
                    if len(fixups) == 0:
                        raise Exception("Assertion failed: out of fixups")
                    
                    #EDGE CASE: All our fixups are 2 bytes, but we could be
                    #straddling a bank boundary. If so, break up the symbol
                    if start_offset >= 0x3FFF:
                        still_need_to_print_high_byte = True
                        cur_chunk_size = 1

                        print(f"    db (({fixups[0][1]} - $C400) >> 1) & $FF", file=datum_section)
                    elif still_need_to_print_high_byte:
                        # We have to run through the loop twice for the other
                        # half of the symbol so that the bank accounting logic
                        # gets to run
                        still_need_to_print_high_byte = False
                        cur_chunk_size = 1

                        print(f"    db (({fixups[0][1]} - $C400) >> 1) >> 8", file=datum_section)
                        fixups.pop(0)
                    else: #COMMON CASE: we can just use dw
                        cur_chunk_size = 2

                        print(f"    dw ({fixups[0][1]} - $C400) >> 1", file=datum_section)
                        fixups.pop(0)
                
                written_chunk_size += cur_chunk_size
                start_offset += cur_chunk_size
                if start_offset >= 0x4000:
                    start_offset -= 0x4000
                    start_bank += 1
                    
                    datum_data = []

                    print(f"SECTION \"BugFS Data {start_bank}\", ROMX[$4000], BANK[{start_bank}]", file=datum_section)
        
        #Build the BFS directory structure
        start_bank = dirbank
        directory = b"".join(directory)

        while len(directory) > 0:
            print(f"SECTION \"BugFS Directory {start_bank}\", ROMX[$4000], BANK[{start_bank}]", file=datum_section)
            if start_bank == dirbank:
                print(f"BugFS_Directory::", file=datum_section)
            
            print_binary_data_as_source(directory[:0x4000], file=datum_section)
            directory = directory[0x4000:]
            start_bank += 1

        return datum_section.getvalue()