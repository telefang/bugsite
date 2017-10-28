def metrics_table(charwidths, string_enc):
    """Given a list of character widths, produce a binary metrics table.
    
    The binary metrics table is for use exclusively with the VWF patched into
    the English translated version of Network Adventure Bugsite.
    
    If a width is not specified for a particular character in charwidths, it
    will default to 8."""
    
    widmap = {}
    
    for charastr, width in charwidths:
        for chara in charastr:
            chara = string_enc(chara)
            widmap[chara] = width
    
    encoded_metrics = [8] * 0xFF
    
    specified_keys = list(widmap.keys())
    specified_keys.sort()
    
    for bytekey in specified_keys:
        encoded_metrics[ord(bytekey)] = widmap[bytekey]
    
    return encoded_metrics

def metrics_length(encoded_metrics, string_enc):
    """Given the encoded font metrics, produce a length calculation function.
    
    The returned function can be called with a string to produce what length
    that character should be. We will use the encoded representation of that
    string to produce a final width."""
    
    def strphyslen(strorbytes):
        if type(strorbytes) is str:
            strorbytes = string_enc(strorbytes)
        
        if type(strorbytes) is int:
            strorbytes = chr(strorbytes)
        
        sum_width = 0
        
        for byte in strorbytes:
            sum_width += encoded_metrics[ord(byte)]
        
        return sum_width
    
    return strphyslen