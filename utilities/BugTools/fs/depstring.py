from BugTools.fs.parser import Filename

def depstring(parselist, basedir):
    """Convert a parsed .bfs listing into a depstring for the Makefile.

    basedir is the directory to look for files in. It may be a single string or
    a list. Paths mentioned within parselist may reside in any of the listed
    directories. If a file is not present in any of those directories, we will
    append the first basedir in the list. Basedir may be a single string if only
    one directory is to be used."""
    deps = set()

    #If only one basedir is provided, list it up anyway
    if type(basedir) is not list:
        basedir = [basedir]

    for command in parselist:
        if type(command) is Filename:
            for base in basedir:
                try:
                    with open(base + "/" + command.path, 'rb') as file:
                        deps.add(base + "/" + command.path)
                        break
                except FileNotFoundError:
                    continue
            else:
                #File missing, which means it needs to be built in the build dir
                deps.add(basedir[0] + "/" + command.path)

    return " ".join(deps)
