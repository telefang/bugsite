from BugTools.fs.parser import bfs_grammar, BFSVisitor
from CodeModule.asm.rgbds import Rgb2
from BugTools.fs.passes import Directory

y = """
    M_BugVM_Sec000: "script/unknown_bvm/0.bvm"
    M_BugVM_Sec001: "script/unknown_bvm/1.bvm"
    """

print(bfs_grammar.parse(y))
print(BFSVisitor().visit(bfs_grammar.parse(y)))

x = Rgb2()
x.load(open("../build/component/bugvm/decode.o", "rb"))

print (x.core)
