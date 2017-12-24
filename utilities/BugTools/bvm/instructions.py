opcodes = {
    "NOP": 0x00,
    "ARFREE": 0x03,
    "STR": 0x06,
    "SUML": 0x07,
    "ANDL": 0x08,
    "OR": 0x09,
    "XOR": 0x0A,
    "AND": 0x0B,
    "CMP_EQ": 0x0C,
    "CMP_NEQ": 0x0D,
    "CMP_LT": 0x0E,
    "CMP_LEQ": 0x0F,
    "CMP_GT": 0x10,
    "CMP_GEQ": 0x11,
    "SLA": 0x13,
    "SUB": 0x14,
    "ADD": 0x15,
    "MOD": 0x16,
    "DIV": 0x17,
    "MUL": 0x18,
    "INDIR": 0x1D,
    "PRED": 0x1E,
    "POPALL": 0x2C,
    "NPREF": 0x36, #technically a prefix, but it does nothing
    "JMPT": 0x37,
    "JMP": 0x38,
    "RET": 0x39,
    "IMMED": 0x3D,
    "DB": 0x3E,
    "JAL": 0x3F, #TODO: Shouldn't this be CALL?
    "PRINT": 0x4C,
    "SCRCURS": 0x50,
    "WINCLR": 0x5B,
    "RESLD": 0x5F,
    "WINWAIT": 0x60,
    "SPRINPUT": 0x61,
    "FARCALL": 0x6A,
    "FARJMP": 0x6B,
    "TILELD": 0x72,
    "PALLD": 0x75,
    "SPRWAITALL": 0x79,
    "WINCOORD": 0x7D,
    "WINCURS": 0x7E,
    "WINBRK": 0x82,
    "TMAPSAV": 0x86, #heeeeeeh
    "SPRWIPE": 0x8E,
    "PRKEY": 0x9F,
    "BLKKEY": 0xA0,
    "PRMOVE": 0xA1,
    "BLKMOVE": 0xA2,
    "PRNAME": 0xA5,
    "SPRCTRL": 0xA6,
    "SPRFINISH": 0xA7,
    "PRMON": 0xAF,
    "NTSTR": 0xB0,
    "NTPRINT": 0xB1,
    "WINOPEN": 0xB2,
    "WINFRAME": 0xB3,
    "BLKMON": 0xBB,
    "RESET": 0xBD,
    "SPRWAIT": 0xC6,
    "SPRHIDE": 0xCF,
    "SPRHOLD": 0xD2,
    "WININPUT": 0xD9,
    "BLKCHIP": 0xE2,
    "PRCHIP": 0xE3,
    "PRNICK": 0xE5,
    "BLKENC": 0xF1,
    "FGAME": 0xFF #will crash everything horribly all the time
}
