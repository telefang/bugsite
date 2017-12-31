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
            output_row.append(BYTE.unpack(tmapbin_file.read(1))[0])
            output_row.append(BYTE.unpack(tmapbin_file.read(1))[0])

        output.append(output_row)

    return output

def write_btmap(tmap_data, btmap_file):
    writer = csv.writer(btmap_file)

    for row in tmap_data:
        output_row = []

        for cell in row:
            output_row.append("$%02X" % cell)

        writer.writerow(output_row)
