<?php

function disassemble_linkage_section($indexid, $resource_segment, $rom_data_str) {
    // The current opcode to instruction table.
    $instructions=array(
        'NOP','ENOP $1','ENOP $2','UO $3','ENOP $4','ENOP $5','STR','SUML','ANDL','OR','XOR','AND','CMP_EQ','CMP_NEQ','CMP_LT','CMP_LEQ',
        'CMP_GT','CMP_GEQ','UO $12','SLA','SUB','ADD','MOD','DIV','MUL','PNOP $19','PNOP $1a','PNOP $1b','PNOP $1c','INDIR','PRED','ENOP $1f',
        'ENOP $20','ENOP $21','ENOP $22','ENOP $23','ENOP $24','ENOP $25','ENOP $26','ENOP $27','ENOP $28','ENOP $29','ENOP $2a','ENOP $2b','POPALL','ENOP $2d','ENOP $2e','PNOP $2f',
        'PNOP $30','PNOP $31','PNOP $32','PNOP $33','PNOP $34','PNOP $35','NPREF','JMPT','JMP','RET','PNOP $3a','PNOP $3b','PNOP $3c','IMMED','DB','JAL',
        'PNOP $40','PNOP $41','ENOP $42','ENOP $43','PNOP $44','PNOP $45','PNOP $46','UO $47','UO $48','PNOP $49','UO $4a','UO $4b','UO $4c','UO $4d','UO $4e','UO $4f',
        'UO $50','UO $51','UO $52','UO $53','PNOP $54','PNOP $55','PNOP $56','PNOP $57','UO $58','UO $59','UO $5a','UO $5b','UO $5c','UO $5d','UO $5e','UO $5f',
        'UO $60','UO $61','UO $62','UO $63','ENOP $64','UO $65','ENOP $66','UO $67','UO $68','UO $69','UO $6a','UO $6b','UO $6c','UO $6d','UO $6e','UO $6f',
        'UO $70','UO $71','UO $72','ENOP $73','UO $74','UO $75','UO $76','UO $77','UO $78','UO $79','UO $7a','UO $7b','UO $7c','UO $7d','UO $7e','UO $7f',
        'UO $80','ENOP $81','UO $82','ENOP $83','PNOP $84','UO $85','UO $86','PNOP $87','UO $88','PNOP $89','PNOP $8a','PNOP $8b','UO $8c','UO $8d','UO $8e','UO $8f',
        'PNOP $90','PNOP $91','UO $92','PNOP $93','PNOP $94','PNOP $95','PNOP $96','ENOP $97','ENOP $98','PNOP $99','ENOP $9a','PNOP $9b','PNOP $9c','UO $9d','UO $9e','UO $9f',
        'UO $a0','UO $a1','UO $a2','UO $a3','UO $a4','UO $a5','UO $a6','UO $a7','UO $a8','PNOP $a9','PNOP $aa','UO $ab','UO $ac','UO $ad','PNOP $ae','UO $af',
        'UO $b0','UO $b1','UO $b2','UO $b3','UO $b4','UO $b5','UO $b6','UO $b7','UO $b8','UO $b9','UO $ba','UO $bb','UO $bc','RESET','UO $be','UO $bf',
        'UO $c0','UO $c1','PNOP $c2','PNOP $c3','UO $c4','UO $c5','UO $c6','UO $c7','UO $c8','UO $c9','PNOP $ca','UO $cb','UO $cc','PNOP $cd','UO $ce','UO $cf',
        'UO $d0','UO $d1','UO $d2','ENOP $d3','ENOP $d4','PNOP $d5','PNOP $d6','PNOP $d7','PNOP $d8','UO $d9','UO $da','UO $db','UO $dc','UO $dd','UO $de','ENOP $df',
        'UO $e0','UO $e1','UO $e2','UO $e3','UO $e4','UO $e5','UO $e6','UO $e7','UO $e8','UO $e9','UO $ea','UO $eb','UO $ec','UO $ed','UO $ee','UO $ef',
        'UO $f0','UO $f1','UO $f2','UO $f3','UO $f4','UO $f5','UO $f6','UO $f7','UO $f8','UO $f9','UO $fa','EFGAME $fb','EFGAME $fc','EFGAME $fd','EFGAME $fe','FGAME'
    );

    // Most instructions are one-byte affairs, this notes the exceptions and assigns them a type identifier.
    $instructiontypes=array(
        'IMMED'=>2,
        'DB'=>3,
        'JMPT'=>5,
        'JMP'=>5,
        'JAL'=>5,
        'NPREF'=>4
    );

    $nul = chr(0);
    $utf16_break = chr(13).$nul.chr(10).$nul;

    // The bank number.
    $sectionbank = ord($resource_segment[0]);
    // The address from the start of the bank.
    $sectionbankoffset = (ord($resource_segment[2])*256)+ord($resource_segment[1]);
    // The physical address from the start of the rom.
    $sectionaddr = ($sectionbank*16384)+$sectionbankoffset;
    // The length of the data associated with this index number.
    $sectionlength = (ord($resource_segment[4])*256)+ord($resource_segment[3]);
    // The data associated with this index number as a string.
    $sectionstr = substr($rom_data_str, $sectionaddr, $sectionlength);
    $c = strlen($sectionstr);
    // Safeguard to stop the reading of a DB string past the end of the data segment.
    $sectionstr .= $nul . $nul;

    $i = 0;
    $storeprefix='';
    $storeprefixoffset=0;
    $lines=array();
    $asmfile='';
    $tabfile='';
    $jumppointprefix='.sub_'.strtolower(dechex($indexid)).'_';
    $stringkeyprefix='STR_'.strtoupper(dechex($indexid)).'_';

    $jumppoints=array();
    while ($i < $c) {
        // Get the instruction sans arguments.
        $instructionoffset=$i;
        $opcode=ord($sectionstr[$i]);
        $instruction=$instructions[$opcode];
        // Determine how the instruction should be read and rendered.
        $instructiontype=0;
        if (isset($instructiontypes[$instruction])) {
            $instructiontype=$instructiontypes[$instruction];
        }

        $eins='';
        $oj=false;
        switch ($instructiontype) {
            case 1: // Single byte operand (this type is unused, but included for the sake of completion).
                $i++;
                $operand=ord($sectionstr[$i]);
                $eins=$instruction.' $'.dechex($operand);
                break;
            case 5: // Jump to offset.
                $oj=true;
            case 2: // Double byte operand.
                $i++;
                $operand=ord($sectionstr[$i]);
                $i++;
                $operand+=ord($sectionstr[$i])*256;
                $eins=$instruction.' $'.dechex($operand);

                // If this is a jump instruction then we should be using labels instead.
                if ($oj) {
                    // Note the jump point so that we can label it later.
                    if (!in_array($operand, $jumppoints)) {
                        $jumppoints[]=$operand;
                    }
                    if ($operand<$c) {
                        // The jump address is commented here in case the jump point can't be labeled.
                        $eins=$instruction.' '.$jumppointprefix.strtolower(dechex($operand)).' ;$'.strtolower(dechex($operand));
                    } else {
                        // A safeguard. Only fires if the jump is outside of the data section.
                        $eins=$instruction.' $'.strtolower(dechex($operand)).' ;Points outside of the section.';
                    }
                }
                break;
            case 3:
                // String.
                $i++;
                $csvstr='';
                // Read bytes until we get a null byte.
                while ($operand=ord($sectionstr[$i])) {
                    // Build a unicode string using the character table.
                    $csvstr.=$csvtable[$operand];
                    $i++;
                }
                if (!empty($storeprefix)) {
                    $instructionoffset=$storeprefixoffset;
                }
                // Create a unique key for the string.
                $stringkey = $stringkeyprefix.strtoupper(dechex($instructionoffset));
                // Add the key to the instruction.
                $eins = $instruction.' '.$stringkey."\n";
                // Build a single row of the text table bugvm.txt.
                $tabfile .= implode($nul, str_split($stringkey, 1)) . $nul . '	' . $nul . '"' . $nul . $csvstr . '"' . $nul . $utf16_break;
                break;
            case 4:
                // Prefix.
                if (empty($storeprefix)) {
                    $storeprefixoffset=$i;
                }
                $storeprefix.=$instruction.' ';
                break;
            default:
                // Everything else.
                $eins=$instruction;
                break;
        }
        // Logic for storing and stacking prefixes.
        if ($instructiontype!=4) {
            if (!empty($storeprefix)) {
                $eins=$storeprefix.$eins;
                $storeprefix='';
                $instructionoffset=$storeprefixoffset;
            }
            $lines[$instructionoffset]=$eins;
        }
        $i++;
    }
    // If the data section ends with a prefix then lets output the prefix or prefix stack by itself.
    if (!empty($storeprefix)) {
        $lines[$storeprefixoffset]=trim($storeprefix);
    }
    // Iterate through each line and apply jump labels.
    foreach ($lines as $lineoffset => $line) {
        if (in_array($lineoffset, $jumppoints)) {
            $asmfile .= "\n" . $jumppointprefix . strtolower(dechex($lineoffset)) . "\n";
        }
        $asmfile .= '    ' . $line . "\n";
    }

    return array($asmfile, $tabfile);
}

function disassemble_rom($filename) {
    $nul = chr(0);
    $utf16_break = chr(13).$nul.chr(10).$nul;

    $files_list = array();
    $tabfile='';

    // Unicode byte-order header.
    $tabfile .= chr(255) . chr(254);

    //A modified single-column UTF-16 csv file that acts as a character table.
    //Splitting the file by linebreaks means that I now have a character code to character lookup table.
    $csvtable= explode($utf16_break, file_get_contents('script/charmap.bin'));

    // Read the rom contents into a string.
    $romasstr = file_get_contents($filename);

    // Read and split the index into 8-byte segments.
    $index = str_split(substr($romasstr, 163840, 32768), 8);

    foreach ($index as $indexid => $indexsegment) {
        // 500 and higher are static resouces, so lets ignore them.
        if ($indexid < 500) {
            $ret = disassemble_linkage_section($indexid, $indexsegment, $romasstr);
            $asmfile = $ret[0];
            $tabfile .= $ret[1];

            // Save this data section in its own file.
            $files_list['script/unknown_bvm/'.dechex($indexid).'.bvm'] = $asmfile;
        }
    }

    // Save the strings
    $files_list['script/bugvm_strings.txt'] = $tabfile;

    return $files_list;
}

/**
 * Merge multiple filesets together.
 * Files that are identical between both sets keep their filename.
 * Files that are different will be prefixed with
 */
function merge_fileset($files1, $files1_prefix, $files2, $files2_prefix) {
    $files1_keys = array_keys($files1);
    $files2_keys = array_keys($files2);
    $files_keys = array_unique(array_merge($files1_keys, $files2_keys));

    $merged_files = array();

    foreach ($files_keys as $delta => $filekey) {
        if ($files1[$filekey] === $files2[$filekey]) {
            $merged_files[$filekey] = $files1[$filekey];
        } else {
            $f1key = $files1_prefix . $filekey;
            $f2key = $files2_prefix . $filekey;

            $merged_files[$f1key] = $files1[$filekey];
            $merged_files[$f2key] = $files2[$filekey];
        }
    }

    return $merged_files;
}

function write_fileset($files) {
    foreach ($files as $fkey => $fstr) {
        file_put_contents($fkey, $fstr);
    }
}

write_fileset(merge_fileset(disassemble_rom('baseroms/baserom_alpha.gbc'), 'versions/alpha/',
                            disassemble_rom('baseroms/baserom_beta.gbc'), 'versions/beta/'));
