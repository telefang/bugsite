from BugTools.bpal.parser import PaletteEntry

def palette_encode(pallist):
    """Convert parsed palette instructions into writable palette data."""

    pdata = []

    for instr in pallist:
        if type(instr) is not PaletteEntry:
            continue

        for color in instr.colors:
            pint = 0

            pint |= color.r >> 3
            pint |= (color.g >> 3) << 5
            pint |= (color.b >> 3) << 10

            pdata.append(bytes([pint & 0xFF, pint >> 8]))

    return b"".join(pdata)
