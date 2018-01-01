import csv, struct

LE16 = struct.Struct("<H")
BYTE = struct.Struct("<B")

def unserialize_tilemap(tmapbin_file):
    #Read width and height
    width = BYTE.unpack(tmapbin_file.read(1))[0]
    height = BYTE.unpack(tmapbin_file.read(1))[0]

    output = []

    for i in range(0,height):
        output_row = []

        for j in range(0,width):
            tile = BYTE.unpack(tmapbin_file.read(1))[0]
            attrs = BYTE.unpack(tmapbin_file.read(1))[0]

            if attrs & 0x08 != 0:
                tile ^= 0x100
                attrs ^= 0x08

            output_row.append(tile)
            output_row.append(attrs)

        output.append(output_row)

    return output

def write_btmap(tmap_data, btmap_file):
    writer = csv.writer(btmap_file)

    for row in tmap_data:
        output_row = []

        for j in range(0, len(row), 2):
            output_row.append("$%03X" % row[j])
            output_row.append("$%02X" % row[j+1])

        writer.writerow(output_row)
