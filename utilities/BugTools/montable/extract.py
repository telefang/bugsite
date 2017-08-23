def extract_bugnames_from_block(romfile, bank, count, decoder):
    """Given a rom file and a bank number, extract bug names from that bank.

    decoder is a function that accepts Bugsite encoding strings and returns
    Python strings.

    bank is the ID of the bank to rip. (Usually 4 or 5)

    count is how many strings to rip. (Usually 0x4000 // 0x40)

    Return value consists of a 2D array of string symbols and decoded strings.
    Suitable for CSV writeout."""

    curpos = romfile.tell()

    block = []

    romfile.seek(bank * 0x4000 + 0x30)

    block_sym = "NAME_%X_" % (bank,)
    for i in range(0, count):
        encoded_name = romfile.read(0x10)

        null_filtered_name = []

        for char in encoded_name:
            if char == 0:
                break
            else:
                null_filtered_name.append(bytes([char]))

        block.append(["%s%X" % (block_sym, i * 0x40 + 0x30), decoder(b"".join(null_filtered_name))])

        _ = romfile.read(0x30)

    romfile.seek(curpos)

    return block
