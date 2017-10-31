def parse_rgbds_symbols(symbol_str):
    """Given an RGBDS .sym file, parse it, and return the resulting parsed data.
    
    List returned will consist of 3-tuples consisting of native bank, native
    address, and symbol name."""
    
    symbols = []
    
    for line in symbol_str.split("\n"):
        line = line.strip()
        
        #filter comments...
        line = line.split(";")[0]
        
        line = line.split(" ")
        if len(line) < 2:
            continue
        
        fulladdr, symname = line
        
        fulladdr = fulladdr.split(":")
        if len(fulladdr) < 2:
            continue
        
        bank, addr = fulladdr
        
        bank = int(bank, 16)
        addr = int(addr, 16)
        
        symbols.append((bank, addr, symname))
    
    return symbols