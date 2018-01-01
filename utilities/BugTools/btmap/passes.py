import csv, math

def read_btmap(btmap_file):
    reader = csv.reader(btmap_file)

    output = []

    for row in reader:
        output_row = []

        for cell in row:
            if cell[0] == "$":
                output_row.append(int(cell[1:], 16))
            else:
                output_row.append(int(cell, 10))

        if len(output_row) == 0:
            continue

        output.append(output_row)

    return output

def serialize_tilemap(tmap_data):
    """Serialize tilemap data.

    The tilemap must be a rectangular 2D array with entries being integers
    within normal byte ranges (0-255)."""

    height = len(tmap_data)
    width = len(tmap_data[0])
    for row in tmap_data:
        if len(row) != width:
            raise SyntaxError("Non-square tilemap")

    byteout = [math.floor(width / 2), height]

    for row in tmap_data:
        for j in range(0, len(row), 2):
            tile = row[j]
            attrs = row[j+1]

            if tile & 0x100 != 0:
                attrs ^= 0x08
                tile ^= 0x100

            byteout.append(tile)
            byteout.append(attrs)

    return bytes(byteout)
