import csv

def parse_stringtbl(infile, language):
    """Parse a list of string equates for use by the .bvm assembler.

    The parsed equates dict will only contain the language specified in the
    language parameter, which should match the heading row."""

    known_equates = {}

    reader = csv.reader(infile)
    lblrow = strrow = None
    for row in reader:
        lblrow = row.index("Label")
        strrow = row.index(language)

        if lblrow is not None and strrow is not None:
            break
    else:
        #CSV was empty or had no header
        return known_equates

    for row in reader:
        sym = row[lblrow]
        decl = row[strrow]

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

def effective_strlen(encoded_bytes, string_enc, string_wid = None):
    """Given a Bugsite encoded string, determine it's effective length.
    
    Returns a length in pixels. We assume fixed-width formatting for now. If you
    are compiling strings with a variable-width font, provide string_wid as a
    len-like function (takes a string, returns an int). You can obtain such a
    function from BugTools.bfont.passes.metrics_length if you have font metrics.
    
    This function takes into account the player's name as an 8-character wide
    symbol, even if it may be shorter in practice. We ask for a string enocder
    so that we can determine what the encoded form of it is."""
    
    if string_wid is None:
        string_wid = lambda x: 8 * len(x)
    
    pname_symbol = string_enc("[name]")
    newline_symbol = string_enc("\n")
    px_width = 0
    
    for byte in encoded_bytes:
        if byte == newline_symbol[0]:
            #Newlines are technically 0 width, even though they add a line and
            #really shouldn't even be present here...
            continue
        elif byte == pname_symbol[0]:
            #We have to assume the worst with the player name...
            px_width += 8 * 8
        else:
            #Every other character is one tile for now.
            px_width += string_wid(byte)
    
    return px_width