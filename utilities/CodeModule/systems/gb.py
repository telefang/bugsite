from CodeModule.exc import *
from CodeModule.asm import linker
from CodeModule.systems.helper import BasePlatform

import math, os, struct

class FlatMapper(BasePlatform):
    ROM = {"segsize":0x8000,
           "views":[(0, 0)],
           "maxsegs":1,
           "type":linker.PermenantArea}
    SRAM = {"segsize":0x2000,
           "views":[(0xA000, 0)],
           "maxsegs":1,
           "type":linker.PermenantArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address and stream name."""

        if addr < 0x8000:
            return (addr, "ROM")
        elif addr > 0x9FFF and addr < 0xC000:
            return ((addr - 0x9FFF), "SRAM")
        else:
            return super(FlatMapper, self).banked2flat(bank, addr)


class MBC1Mapper(BasePlatform):
    ROM = {"segsize":0x4000,
           "views":[(0, 0), (0x4000, (1, 0x80))],
           "maxsegs":0x80,
           "unusable":[(None, 0x20), (None, 0x40), (None, 0x60)],
           "type":linker.PermenantArea}
    SRAM = {"segsize":0x2000,
           "views":[(0xA000, None)],
           "maxsegs":4,
           "type":linker.PermenantArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address."""

        if addr < 0x8000 and bank < 0x80:
            if bank == 0x20 or bank == 0x40 or bank == 0x60 or bank == 0:
                bank += 1

            if addr < 0x4000:
                bank = 0
            else:
                addr -= 0x4000

            return (bank * 0x4000 + addr, "ROM")
        elif addr > 0x9FFF and addr < 0xC000 and bank < 0x04:
            addr -= 0xA000

            return (bank * 0x1000 + addr, "SRAM")
        else:
            return super(MBC1Mapper, self).banked2flat(bank, addr)

class MBC2Mapper(BasePlatform):
    ROM = {"segsize":0x4000,
           "views":[(0, 0), (0x4000, (1, 0x10))],
           "maxsegs":0x10,
           "unusable":[(None, 0x20), (None, 0x40), (None, 0x60)],
           "type":linker.PermenantArea}
    SRAM = {"segsize":0x200,
           "views":[(0xA000, 0)],
           "maxsegs":1,
           "type":linker.PermenantArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address."""

        if addr < 0x8000 and bank < 0x10:
            if addr < 0x4000:
                bank = 0
            else:
                addr -= 0x4000

            return (bank * 0x4000 + addr, "ROM")
        elif addr > 0x9FFF and addr < 0xA200 and bank == 0:
            addr -= 0xA000

            return (addr, "SRAM")
        else:
            return super(MBC2Mapper, self).banked2flat(bank, addr)

class MBC3Mapper(BasePlatform):
    ROM = {"segsize":0x4000,
           "views":[(0, 0), (0x4000, (1, 0x80))],
           "maxsegs":0x80,
           "type":linker.PermenantArea}
    SRAM = {"segsize":0x2000,
           "views":[(0xA000, None)],
           "maxsegs":4,
           "type":linker.PermenantArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address."""

        if addr < 0x8000 and bank < 0x80:
            if addr < 0x4000:
                bank = 0
            else:
                addr -= 0x4000

            return (bank * 0x4000 + addr, "ROM")
        elif addr > 0x9FFF and addr < 0xC000 and bank < 0x04:
            addr -= 0xA000

            return (bank * 0x1000 + addr, "SRAM")
        else:
            return super(MBC3Mapper, self).banked2flat(bank, addr)

class MBC5Mapper(BasePlatform):
    ROM = {"segsize":0x4000,
           "views":[(0, 0), (0x4000, (1, 0x200))],
           "maxsegs":0x200,
           "type":linker.PermenantArea}
    SRAM = {"segsize":0x2000,
           "views":[(0xA000, None)],
           "maxsegs":0x10,
           "type":linker.PermenantArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address.

        This MBC5 implementation supports 64mbit cartridges, which were never
        released by Nintendo but are mentioned in the GBPM. Some EMS flashcarts
        are 64mbit, but allow you to boot to the first or second half of that
        memory space through reset-counting hardware."""

        if addr < 0x8000 and bank < 0x200:
            if addr < 0x4000:
                bank = 0
            else:
                addr -= 0x4000

            return (bank * 0x4000 + addr, "ROM")
        elif addr > 0x9FFF and addr < 0xC000 and bank < 0x10:
            addr -= 0xA000

            return (bank * 0x1000 + addr, "SRAM")
        else:
            return super(MBC5Mapper, self).banked2flat(bank, addr)

class BaseSystem(BasePlatform):
    MEMAREAS = ["ROM", "VRAM", "SRAM", "WRAM", "HRAM", "OAM", "ECHO", "IOSPACE", "INTMASK"]
    IOSPACE = {"views":[(0xFF00, 0)],
               "segsize":128,
               "maxsegs":1,
               "type":linker.DynamicArea}
    INTMASK = {"views":[(0xFFFF, 0)],
               "segsize":1,
               "maxsegs":1,
               "type":linker.DynamicArea}
    HRAM = {"views":[(0xFF80, 0)],
            "segsize":127,
            "maxsegs":1,
            "type":linker.DynamicArea}
    OAM = {"views":[(0xFE00, 0)],
           "segsize":0xA0,
           "maxsegs":1,
           "type":linker.DynamicArea}
    ECHO = {"views":[(0xE000, 0)],
            "segsize":0x1E00,
            "type":linker.ShadowArea,
            "shadows":"WRAM"}
    GROUPMAP = {"CODE": "ROM", "DATA": "ROM", "BSS":"WRAM", "HOME":("ROM", 0), "VRAM":"VRAM", "HRAM":"HRAM"}

    def banked2flat(self, bank, addr):
        if addr > 0xFDFF and addr < 0xFEA0:
            return (addr - 0xFE00, "OAM")
        elif addr > 0xFEFF and addr < 0xFF80:
            return (addr - 0xFF00, "IOSPACE")
        elif addr > 0xFF7F and addr < 0xFFFF:
            return (addr - 0xFF80, "HRAM")
        elif addr > 0xDFFF and addr < 0xFE00:
            newresp = self.banked2flat(addr - 0x2000)
            return (newresp[0], "ECHO")
        elif addr == 0xFFFF:
            return (0, "INTMASK")
        else:
            return super(BaseSystem, self).banked2flat(bank, addr)

class CGB(BaseSystem):
    WRAM = {"segsize":0x1000,
            "views":[(0xC000, 0), (0xD000, (1, 0x8))],
            "maxsegs":8,
            "type":linker.DynamicArea}
    VRAM = {"segsize":0x2000,
            "views":[(0x8000, None)],
            "maxsegs":2,
            "type":linker.DynamicArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address."""
        if addr > 0x7FFF and addr < 0xA000 and bank < 2:
            return (bank * 0x2000 + addr - 0x8000, "VRAM")
        elif addr > 0xBFFF and addr < 0xE000 and bank < 8:
            if addr < 0xC000:
                bank = 0
            else:
                addr -= 0x1000

            addr -= 0xC000
            return (bank * 0x1000 + addr, "WRAM")
        else:
            return super(BaseSystem, self).banked2flat(bank, addr)

class DMG(BaseSystem):
    WRAM = {"segsize":0x2000,
            "views":[(0xC000, 0)],
            "maxsegs":1,
            "type":linker.DynamicArea}
    VRAM = {"segsize":0x2000,
            "views":[(0x8000, 0)],
            "maxsegs":1,
            "type":linker.DynamicArea}

    def banked2flat(self, bank, addr):
        """Convert a Gameboy bank number and Z80 address to a flat ROM address."""
        if addr > 0x7FFF and addr < 0xA000:
            return (addr - 0x8000, "VRAM")
        elif addr > 0xBFFF and addr < 0xE000:
            return (addr - 0xC000, "WRAM")
        else:
            return super(BaseSystem, self).banked2flat(bank, addr)

MAPPERLIST = {"flat":(FlatMapper, None),
    "mbc1":(MBC1Mapper, None),
    "mbc2":(MBC2Mapper, None),
    "mbc3":(MBC3Mapper, None),
    "mbc5":(MBC5Mapper, None)}

VARIANTLIST = {"dmg":(DMG, MAPPERLIST),
    "gb":(DMG, MAPPERLIST),
    "cgb":(CGB, MAPPERLIST),
    "gbc":(CGB, MAPPERLIST)}

def GameboyLinker(variant1, variant2):
    class GameboyLinkerInstance(linker.Linker, variant1, variant2):
        pass

    return GameboyLinkerInstance

def flat2banked(flataddr):
    """Convert a flat address to a Gameboy Bank number and Z80 address."""

    bank = math.floor(flataddr / 0x4000)
    addr = flataddr - bank * 0x4000

    if bank > 0:
        addr += 0x4000

    return (bank, addr)

#this is all dead code :/

Z80INT = struct.Struct("<H")
Z80CHAR = struct.Struct("<B")

class ROMImage(object):
    class ROMBank (object):
        """File-like object wrapper for banked ROM accesses."""
        def __init__(self, parent, fileobj, bank = 0, mbcver = 3):
            self.__parent = parent
            self.__fobj = fileobj
            self.__open = True
            self.__bank = bank
            self.__fptr = 0
            self.__mbcver = mbcver

        def __makerange(self, nbytes):
            hbegin = 0
            hsize = 0
            bbegin = 0
            bsize = 0

            if self.__fptr < 0x4000:
                hbegin = self.__fptr
                if self.__fptr + bytes > 0x3FFF:
                    hsize = 0x4000 - hbegin
                    bbegin = banked2flat(self.__bank, 0x4000, self.__mbcver)
                    bsize = min(bytes - hsize, 0x4000)
                else:
                    hsize = bytes
            elif self.__fptr < 0x8000:
                bbegin = banked2flat(self.__bank, self.__fptr, self.__mbcver)
                bsize = min(bytes, 0x8000 - self.__fptr)

            return (hbegin, hsize, bbegin, bsize)

        def close(self):
            #I don't need this, but...
            self.__open = False
            self.__fobj.flush()

        def flush(self):
            if not self.__open:
                raise ValueError()

            self.__fobj.flush()

        def next(self):
            #Not implemented just yet...
            raise NotImplemented()

        def read(self, bytes):
            if not self.__open:
                raise ValueError()

            (hbegin, hsize, bbegin, bsize) = self.__makerange(bytes)

            returned = b""
            if hsize > 0:
                self.__fobj.seek(hbegin, os.SEEK_BEGIN)
                returned += self.__fobj.read(hsize)

            if bsize > 0:
                self.__fobj.seek(bbegin, os.SEEK_BEGIN)
                returned += self.__fobj.read(bsize)

            self.__fptr += hsize + bsize
            return returned

        def seek(self, offset, whence):
            if not self.__open:
                raise ValueError()

            if whence == os.SEEK_BEGIN:
                self.__fptr = offset
            elif whence == os.SEEK_END:
                self.__fptr = 0x8000 + offset
            elif whence == os.SEEK_CUR:
                self.__fptr += offset
            else:
                raise ValueError()

        def tell(self):
            if not self.__open:
                raise ValueError()

            return self.__fptr

        def write(self, target):
            if not self.__open:
                raise ValueError()

            (hbegin, hsize, bbegin, bsize) = self.__makerange(target.size())

            if hsize > 0:
                self.__fobj.seek(hbegin, os.SEEK_BEGIN)
                returned += self.__fobj.write(target[0:hsize])

            if bsize > 0:
                self.__fobj.seek(bbegin, os.SEEK_BEGIN)
                returned += self.__fobj.write(target[hsize:hsize+bsize])

    def __init__(self, fileobj, mbcver = 3):
        self.__fileobj = fileobj
        self.__mbcver  = mbcver

    def bank(self, banknum = 0):
        """Get a file-like object that reads and writes to a particular ROM bank.

        The returned file object will show the HOME bank at 0x4000 and the selected bank at 0x8000."""
        return ROMImage.ROMBank(self, self.__fileobj, banknum, self.__mbcver)

