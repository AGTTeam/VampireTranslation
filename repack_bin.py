import codecs
import os
from hacktools import common
import constants
import game


def run(data):
    infile = data + "extract/arm9.bin"
    outfile = data + "repack/arm9.bin"
    fontdata = data + "font_data.bin"
    binfile = data + "bin_input.txt"
    # datfile = data + "dat_input.txt"
    table, invtable = game.getTable(data)
    glyphs = game.getGlyphs(data)

    if not os.path.isfile(binfile):
        common.logError("Input file", binfile, "not found")
        return

    common.logMessage("Repacking BIN from", binfile, "...")
    # Read all strings
    translations = {}
    strings = {}
    with codecs.open(binfile, "r", "utf-8") as bin:
        section = common.getSection(bin, "")
        chartot, transtot = common.getSectionPercentage(section)
        for jpstr in section:
            if jpstr in section and section[jpstr][0] != "":
                translations[jpstr] = section[jpstr][0]
                if section[jpstr][0] not in strings:
                    strings[section[jpstr][0]] = -1
            elif jpstr not in strings:
                strings[jpstr] = 0

    common.copyFile(infile, outfile)
    with common.Stream(infile, "rb") as fin:
        ptrgroups, allptrs = game.getBINPointerGroups(fin)
        with common.Stream(outfile, "rb+") as f:
            # Write all strings
            f.seek(constants.mainptr["offset"])
            for string in strings:
                writestr = string
                if strings[string] == -1:
                    writestr = common.wordwrap(writestr, glyphs, constants.wordwrap, game.detectTextCode, default=0xa)
                strings[string] = f.tell()
                common.logDebug("Writing string", writestr, "at", common.toHex(f.tell()))
                game.writeString(f, writestr, table)
                f.writeByte(0)
            common.logDebug("Finished at", common.toHex(f.tell()))
            common.logMessage("Room for", common.toHex(constants.mainptr["end"] - f.tell()), "more bytes")
            # Change pointers
            for ptrgroup in ptrgroups:
                for ptr in ptrgroups[ptrgroup]:
                    f.seek(ptr["pos"])
                    fin.seek(ptr["ptr"])
                    if ptr["data"]:
                        jpstr = game.readData(fin, allptrs)
                    else:
                        jpstr = game.readString(fin, invtable, allptrs)
                    if jpstr in translations:
                        jpstr = translations[jpstr]
                    if jpstr not in strings:
                        common.logError("String", jpstr, "not found")
                    else:
                        common.logDebug("Writing pointer", common.toHex(strings[jpstr]), "for string", jpstr, "at", common.toHex(f.tell()))
                        f.writeUInt(0x02000000 + strings[jpstr])

    common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))

    # Export font data and apply armips patch
    with common.Stream(fontdata, "wb") as f:
        for charcode in range(0x9010, 0x908f + 1):
            c = invtable[charcode]
            f.writeByte(glyphs[c].width)
    common.armipsPatch("bin_patch.asm")
