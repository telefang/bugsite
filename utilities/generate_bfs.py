import argparse, os, os.path

def make_filelist(dirname):
    output = {}

    for filename in os.listdir(dirname):
        hexit = int(os.path.splitext(os.path.basename(filename))[0], 16)
        output[hexit] = os.path.join(dirname, filename)

    return output

outlist = {}
outlist.update(make_filelist("..\\graphics\\unknown"))
outlist.update(make_filelist("..\\script\\unknown_res"))

keylist = sorted(outlist.keys())

for key in keylist:
    print ("\"%s\"" % (outlist[key], ))
