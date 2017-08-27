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

    decoder_mapping = {}
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
                elif len(suspected_ligature) > ligature_largest or current_chara == len(instr) - 1:
                    #Not a valid ligature, abandon ligature search
                    current_chara -= len(suspected_ligature) - 1
                    output.append(encoder_mapping[instr[current_chara]])

                    is_ligature = False
                    suspected_ligature = ""
            else:
                output.append(encoder_mapping[chara])

            current_chara += 1

        return b"".join(output)

    def decoder(inbytes):
        output = []

        for byte in inbytes:
            output.append(decoder_mapping[bytes([byte])])

        return "".join(output)

    #Actual parsing starts here
    for line in infile:
        if 'charmap "' not in line:
            continue

        if line[0] == "#":
            continue

        delim_split = line.split('"')
        decoded_char = delim_split[1]
        if decoded_char == u"":
            #Special case: Quoted quotes.
            #   e.g. charmap """, $22

            #This parsing logic sucks arse.
            if len(delim_split) > 3:
                decoded_char = u"\""

        if decoded_char == u"\\n":
            decoded_char = u"\n"

        unparsed_hex = delim_split[-1].split("$")[1].strip()
        bytedata = []

        #This code -technically- means you can have characters that encode to
        #multiple bytes if you use more than 2 hexdigits at a time
        for i in range(0, len(unparsed_hex), 2):
            bytedata.append(int(unparsed_hex[i:i+2], 16) << i // 2)

        if bytes(bytedata) not in decoder_mapping.keys():
            decoder_mapping[bytes(bytedata)] = decoded_char

        if len(decoded_char) > 1:
            ligature_starters.add(decoded_char[0])
            ligature_mapping[decoded_char] = bytes(bytedata)
            ligature_largest = max(ligature_largest, len(decoded_char))
        else:
            encoder_mapping[decoded_char] = bytes(bytedata)

    return encoder, decoder
