from BugTools.bpal.parser import bpal_grammar, PaletteDataVisitor

y = """
        #012345, #67890a, #bcdef0, #123456
    P_MainScript_Theme000: #012345, #67890a, #bcdef0, #123456
    P_MainScript_Theme001: #012345, #67890a, #bcdef0, #123456
    """

#print(bpal_grammar.parse(y))
print(PaletteDataVisitor().visit(bpal_grammar.parse(y)))