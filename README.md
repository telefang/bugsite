A partial disassembly of Bugsite Alpha and Beta versions.

To build, the following ROMs of Network Adventure Bugsite Alpha and Beta
versions are required:

```
$ md5sum baseroms/baserom_alpha.gbc baseroms/baserom_beta.gbc
7f9dbafd6d16957e9687f89e33765f0b *baseroms/baserom_alpha.gbc
3c6b37b6162d599e3554689500b23af1 *baseroms/baserom_beta.gbc
a5fa9f988b32439c8596432f8ec440f7 *baseroms/baserom_patch.gbc
```

baserom_patch.gbc is the last IPS patch (version 26) applied to baserom_beta.gbc
with bytes beyond 0x200000 erased. (The IPS patch mistakenly extends the file by
about 4kb) The total file size should be exactly 0x200000 bytes. When patch
disassembly is completed this file will no longer be needed.

This disassembly uses the `overlay` feature of RGBDS currently only
present in Sanqui's fork: https://github.com/Sanqui/rgbds

(kmeisthax/rgbds works too)