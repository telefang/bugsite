from BugTools.fs.parser import Label, Filename
from CodeModule import cmodel
from CodeModule.asm.rgbds import Rgb2, Rgb2Section, Rgb2Symbol

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

def fsimage(parselist, dirbank = 0xA, databank = 0xC):
    """Construct a series of RGBDS sections corresponding to our filesystem.

    dirbank is the index of the directory structure bank. Directory data will be
    added to this bank according to the BugFS directory structure, for as many
    banks as needed.

    databank is the index of the first data bank. Data from each file will be
    densely packed into each bank. Files will be spanned across bank boundaries
    if needed. The databank index must be greater than the last directory bank
    in use.

    The returned RGB2 object file will contain sections with the filesystem
    data. One symbol will be exposed for the directory."""

    #Filter out the parselist. We only care about file references.
    filepaths = []

    for command in parselist:
        if type(command) is Filename:
            filepaths.append(command.path)

    #Collect all the data into a single array, we'll chop it up later.
    datum = []

    for path in filepaths:
        with open(path, 'rb') as file:
            datum.append(file.read())

    #Construct a directory listing for everything.
    directory = []
    start_bank = databank
    start_offset = 0x0000

    for data in datum:
        new_dir = Directory(basebank = start_bank, baseoffset = start_offset, filesize = len(data))
        directory.append(new_dir.bytes)

        start_offset += len(data)
        while start_offset >= 0x4000:
            start_offset -= 0x4000
            start_bank += 1

    #Build the RGBDS file
    rgb2obj = Rgb2()
    directory = b"".join(directory)
    start_bank = dirbank

    while len(directory) > 0:
        directory_section = Rgb2Section(sectype=Rgb2Section.ROMX) #ROMX section
        directory_section.org = 0x4000
        directory_section.bank = start_bank
        directory_section.datsec.data = directory[:0x4000]

        rgb2obj.sections.append(directory_section)

        directory = directory[0x4000:]
        start_bank += 1

    datum = b"".join(datum)
    start_bank = databank
    while len(datum) > 0:
        datum_section = Rgb2Section(sectype=Rgb2Section.ROMX)
        datum_section.org = 0x4000
        datum_section.bank = start_bank
        datum_section.datsec.data = datum[:0x4000]

        rgb2obj.sections.append(datum_section)

        datum = datum[0x4000:]
        start_bank += 1

    directory_symbol = Rgb2Symbol(name="BugFS_Directory", symtype=Rgb2Symbol.EXPORT)
    directory_symbol.value.sectionid = 0 #Index of what section this symbol is in
    directory_symbol.value.value = 0 #Offset from the start of said section

    rgb2obj.symbols.append(directory_symbol)

    return rgb2obj
