from BugTools.fs.parser import bfs_grammar, BFSVisitor

y = """
    M_File01: "C:\Documents and Settings\file1.bvm"
    "Z:\Another thing"
    """

print(bfs_grammar.parse(y))
print(BFSVisitor().visit(bfs_grammar.parse(y)))
