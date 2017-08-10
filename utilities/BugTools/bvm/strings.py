def parse_stringtbl(infile):
    """Parse a list of string equates for use by the .bvm assembler."""

    known_equates = {}

    for line in infile:
        sym, decl = line.split("\t")

        decl = decl.strip()
        separator = decl[0]
        decl = decl[1:-1]
        decl.replace(separator + separator, separator)

        known_equates[sym] = decl

    return known_equates

def parse_charmap(infile):
    """Parse the character mapping for this ROM.

    Returns a function which can be used as a .bvm string encoder."""

    encoder_mapping = {}

    def encoder(instr):
        output = []

        for byte in instr:
            output.append(encoder_mapping[byte])

        return b"".join(output)

    #Actual parsing starts here
    for encode_slot, line in enumerate(infile):
        decoded_char = line[:-1]

        if len(decoded_char) != 1:
            #We don't (yet) support multicharacter ligatures
            continue

        encoder_mapping[decoded_char] = bytes([encode_slot])

    return encoder
