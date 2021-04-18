import codecs
import os
from hacktools import common
import constants
import game


def run(data, analyze=False):
    infile = data + "extract/arm9.bin"
    outfile = data + "repack/arm9.bin"
    fontdata = data + "font_data.bin"
    binfile = data + "bin_input.txt"
    datfile = data + "dat_input.txt"
    binsize = os.path.getsize(infile)
    table, invtable = game.getTable(data)
    glyphs = game.getGlyphs(data)

    if not os.path.isfile(binfile):
        common.logError("Input file", binfile, "not found")
        return
    if not os.path.isfile(datfile):
        common.logError("Input file", datfile, "not found")
        return

    common.logMessage("Repacking BIN from", binfile, "...")
    # Read all strings
    translations = {}
    strings = {}
    with codecs.open(binfile, "r", "utf-8") as bin:
        section = common.getSection(bin, "")
        chartot, transtot = common.getSectionPercentage(section)
        for jpstr in section:
            if section[jpstr][0] != "":
                translations[jpstr] = section[jpstr][0]
                if section[jpstr][0] not in strings:
                    strings[section[jpstr][0]] = -1
            elif jpstr not in strings:
                strings[jpstr] = 0

    # common.copyFile(infile, outfile)
    with common.Stream(infile, "rb") as fin:
        ptrgroups, allptrs = game.getBINPointerGroups(fin)
        with common.Stream(outfile, "rb+") as f:
            # Write all strings
            f.seek(constants.mainptr["offset"])
            for string in strings:
                writestr = string
                if strings[string] == -1:
                    writestr = writestr.replace("<0A>", "|")
                    writestr = common.wordwrap(writestr, glyphs, constants.wordwrap, game.detectTextCode, default=0xa)
                common.logDebug("Writing string", writestr, "at", common.toHex(f.tell()))
                strings[string] = f.tell()
                game.writeString(f, writestr, table)
                if "<ch1>" in writestr:
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

    common.logMessage("Repacking DAT from", datfile, "...")
    chartot = transtot = 0
    with codecs.open(datfile, "r", "utf-8") as dat:
        with common.Stream(infile, "rb") as fin:
            with common.Stream(outfile, "rb+") as f:
                for datname in constants.datptrs:
                    if type(constants.datptrs[datname]) is not list and "main" in constants.datptrs[datname]:
                        continue
                    section = common.getSection(dat, datname)
                    if len(section) == 0:
                        continue
                    chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
                    datptrs = []
                    if type(constants.datptrs[datname]) is list:
                        for datoffset in constants.datptrs[datname]:
                            datptrs.append(datoffset)
                    else:
                        datptrs.append(constants.datptrs[datname])
                    # Read all strings first
                    allstrings = []
                    for datptr in datptrs:
                        fin.seek(datptr["offset"])
                        if "end" in datptr:
                            while fin.tell() < datptr["end"]:
                                strstart = fin.tell()
                                jpstr = game.readString(fin, invtable)
                                fin.readZeros(binsize)
                                allstrings.append({"start": strstart, "end": fin.tell() - 1, "str": jpstr})
                        else:
                            ptrs = []
                            for i in range(datptr["count"]):
                                ptrpos = fin.tell()
                                ptrs.append({"address": fin.readUInt() - 0x02000000, "pos": ptrpos})
                            for i in range(datptr["count"]):
                                fin.seek(ptrs[i]["address"])
                                strstart = fin.tell()
                                jpstr = game.readString(fin, invtable)
                                fin.readZeros(binsize)
                                allstrings.append({"start": strstart, "end": fin.tell() - 1, "str": jpstr, "ptrpos": ptrs[i]["pos"]})
                    # Check how much space is used by these strings and update them with the translations
                    minpos = 0xffffffff
                    maxpos = 0
                    for jpstr in allstrings:
                        if jpstr["start"] < minpos:
                            minpos = jpstr["start"]
                        if jpstr["end"] > maxpos:
                            maxpos = jpstr["end"]
                        check = jpstr["str"]
                        if check in section and section[check][0] != "":
                            jpstr["str"] = section[check].pop()
                            if len(section[check]) == 0:
                                del section[check]
                    if analyze:
                        allspace = []
                        for i in range(minpos, maxpos + 1):
                            allspace.append(i)
                        for jpstr in allstrings:
                            for i in range(jpstr["start"], jpstr["end"] + 1):
                                allspace.remove(i)
                        common.logMessage(datname)
                        common.logMessage(allspace)
                    # Start writing them
                    f.seek(minpos)
                    for jpstr in allstrings:
                        if "ptrpos" in jpstr and datname != "ItemShop":
                            # Write the string and update the pointer
                            strpos = f.tell()
                            game.writeString(f, jpstr["str"], table, maxpos - f.tell())
                            f.writeUIntAt(jpstr["ptrpos"], strpos + 0x02000000)
                        else:
                            # Try to fit the string in the given space
                            f.seek(jpstr["start"])
                            game.writeString(f, jpstr["str"], table, jpstr["end"] - f.tell())
                            while f.tell() < jpstr["end"]:
                                f.writeByte(0)
    common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))

    # Export font data and apply armips patch
    with common.Stream(fontdata, "wb") as f:
        for charcode in range(0x9010, 0x908f + 1):
            c = invtable[charcode]
            f.writeByte(glyphs[c].width)
    common.armipsPatch("bin_patch.asm")
