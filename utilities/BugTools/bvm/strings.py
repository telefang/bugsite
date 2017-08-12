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
    ligature_starters = set()
    ligature_mapping = {}
    ligature_largest = 0

    def encoder(instr):
        output = []

        is_ligature = False
        suspected_ligature = ""

        current_chara = 0

        while current_chara < len(instr):
            chara = instr[current_chara]

            if chara in ligature_starters:
                is_ligature = True

            if is_ligature:
                suspected_ligature += chara

                if suspected_ligature in ligature_mapping.keys():
                    output.append(ligature_mapping[suspected_ligature])

                    is_ligature = False
                    suspected_ligature = ""
                elif len(suspected_ligature) > ligature_largest:
                    #Not a valid ligature, abandon ligature search
                    current_chara -= len(suspected_ligature)
                    output.append(encoder_mapping[instr[current_chara]])

                    is_ligature = False
                    suspected_ligature = ""
            else:
                output.append(encoder_mapping[chara])

            current_chara += 1

        return b"".join(output)

    #Actual parsing starts here
    for encode_slot, line in enumerate(infile):
        decoded_char = line[:-1]

        if len(decoded_char) > 1:
            ligature_starters.add(decoded_char[0])
            ligature_mapping[decoded_char] = bytes([encode_slot])
            ligature_largest = max(ligature_largest, len(decoded_char))
        else:
            encoder_mapping[decoded_char] = bytes([encode_slot])

    return encoder
