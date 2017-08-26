from CodeModule.asm.rgbds import Rgb5, Rgb5Section

def build_string_object(strlist, encoder):
    """Given a list of string defines, produce an RGBDS object file.

    Only string defines whose symbol starts with NAME_ will be added to the file
    and other symbols classes will be ignored. Additionally, symbols must have a
    bank and offset value in order to be assembled into the file.

    Symbols will be padded to the next 16-byte boundary with zeroes. This
    function is intended for use in altering the standard names within the RPG
    Attribute Tables within Bugsite. For strings embedded in BugVM instruction
    streams, see the BugTools.bvm module."""

    obj = Rgb5()

    for strsym in strlist:
        splitname = strsym[0].split("_")

        if splitname[0] != "NAME":
            continue

        bank = int(splitname[1], 16)
        offset = int(splitname[2], 16)

        sec = Rgb5Section()
        sec.name = "Attr Table Name %X_%X" % (bank, offset)
        sec.sectype = Rgb5Section.ROMX
        sec.org = 0x4000 + offset
        sec.bank = bank
        sec.datsec.data = encoder(strsym[1]) + b"\x00"

        obj.sections.append(sec)

    return obj
