from CodeModule import cmodel

class Directory(cmodel.Struct):
    basebank = cmodel.U8
    baseoffset = cmodel.LeU16
    filesize = cmodel.LeU16
    padding1 = cmodel.U8
    padding2 = cmodel.U8
    padding3 = cmodel.U8

    __order__ = ["basebank", "baseoffset", "filesize", "padding1", "padding2", "padding3"]