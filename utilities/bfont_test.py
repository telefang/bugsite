from BugTools.bfont.parser import bfont_grammar, FontWidthVisitor

y = """
    width '1', 8
    width 'a', 3
    """

#print(bfont_grammar.parse(y))
print(FontWidthVisitor().visit(bfont_grammar.parse(y)))
