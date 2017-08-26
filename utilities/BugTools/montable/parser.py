import csv

def parse_names_list(strfile, language):
    """Parse a file containing a CSV formatted list of attribute-item names.

    The parsed names list will only contain the language specified in the
    language parameter, which should match the heading"""

    output = []

    reader = csv.reader(strfile)
    lblrow = strrow = None
    for row in reader:
        lblrow = row.index("Symbol")
        strrow = row.index(language)

        if lblrow is not None and strrow is not None:
            break
    else:
        #CSV was empty or had no header
        return output

    for row in reader:
        output.append([row[lblrow], row[strrow]])

    return output
