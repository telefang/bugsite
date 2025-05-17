import io
import itertools

def build_string_object(strlist, encoder):
    """Given a list of string defines, produce assembly source.

    Only string defines whose symbol starts with NAME_ will be added to the file
    and other symbols classes will be ignored. Additionally, symbols must have a
    bank and offset value in order to be assembled into the file.

    Symbols will be padded to the next 16-byte boundary with zeroes. This
    function is intended for use in altering the standard names within the RPG
    Attribute Tables within Bugsite. For strings embedded in BugVM instruction
    streams, see the BugTools.bvm module."""

    with io.StringIO() as src:
        for strsym in strlist:
            splitname = strsym[0].split("_")

            if splitname[0] != "NAME":
                continue

            bank = int(splitname[1], 16)
            offset = int(splitname[2], 16)

            encoded_string = encoder(strsym[1])
            
            name = "Attr Table Name %X_%X" % (bank, offset)
            org = 0x4000 + offset

            print(f"SECTION \"{name}\", ROMX[${org:04x}], BANK[${bank}]", file=src)

            for line in itertools.batched(encoded_string, 0x10):
                bytes_written = []
                
                for byte in line:
                    bytes_written.append(f"${byte:02x}")
                
                while len(bytes_written) < 0x10:
                    bytes_written.append("0")
                
                bytes_list = ", ".join(bytes_written)
                print(f"    db {bytes_list}", file=src)

        return src.getvalue()
