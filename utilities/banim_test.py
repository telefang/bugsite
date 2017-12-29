from BugTools.bvm.parser import bvm_grammar, InstrListVisitor

data = """
START LoopSymbol

frame1:
    SPRITEGROUP
    SPRITE $F8,$0,$19,$00
    SPRITE $0,$0,$20,$00,behindbg,vflip,hflip
    ;X, Y, tile, palette, then priority and flipbits
    ;tile is relative to the sprite slot, and continues onward from there
    ;tile IDS greater than $80 (the number of OAM-exclusive tiles) wrap around
    ;to the other VRAM bank, which flips the VRAM bank bit in the attributes.
    ;this scheme is probably only suitable for oversize sprites in slot 0.
    ENDSPRITEGROUP

LoopSymbol:
    FRAME frame1
    WAIT 1
    FRAME frame2
    WAIT $10
    RESRVRIGHT
    RESET
"""

x = bvm_grammar.parse(data + "\n") #Add a newline. Our grammar doesn't like files without ending newlines.

mp = InstrListVisitor().visit(x)

#TODO: make some kind of repr for Bof1 instances
print (mp)
