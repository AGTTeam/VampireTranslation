import codecs
import os
from hacktools import common
import constants
import game


def run(data, copybin=False, analyze=False):
    infile = data + "extract/arm9.bin"
    outfile = data + "repack/arm9.bin"
    fontdata = data + "font_data.bin"
    dictionarydata = data + "dictionary.asm"
    binfile = data + "bin_input.txt"
    datfile = data + "dat_input.txt"
    binsize = os.path.getsize(infile)
    table, invtable = game.getTable(data)
    glyphs, dictionary = game.getGlyphs(data)

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

    if copybin:
        common.copyFile(infile, outfile)
        if os.path.isfile(data + "bmpcache.txt"):
            os.remove(data + "bmpcache.txt")
    with common.Stream(infile, "rb") as fin:
        ptrgroups, allptrs = game.getBINPointerGroups(fin)
        with common.Stream(outfile, "rb+") as f:
            # Write all strings
            outofspace = False
            outchars = 0
            lastgood = 0
            f.seek(constants.mainptr["offset"])
            for string in strings:
                writestr = string
                if strings[string] == -1:
                    if "<ch1>" not in writestr:
                        writestr = writestr.replace("<0A>", "|")
                        writestr = common.wordwrap(writestr, glyphs, constants.wordwrap, game.detectTextCode, default=0xa)
                if outofspace:
                    common.logDebug("Skipping string", writestr)
                    outchars += len(writestr) - writestr.count("<") * 3
                    strings[string] = lastgood
                else:
                    common.logDebug("Writing string", writestr, "at", common.toHex(f.tell()))
                    usedictionary = True
                    if writestr.startswith(">>"):
                        usedictionary = False
                        writestr = game.alignCenter(writestr[2:], glyphs)
                    strings[string] = lastgood = f.tell()
                    game.writeString(f, writestr, table, usedictionary and dictionary or {})
                    if "<ch1>" in writestr:
                        f.writeByte(0)
                    if f.tell() >= constants.mainptr["end"]:
                        outofspace = True
                        common.logMessage("Ran out of space while writing string", writestr)
            common.logDebug("Finished at", common.toHex(f.tell()))
            if outofspace:
                common.logMessage("Characters left out:", outchars)
            else:
                common.logMessage("Room for", common.toHex(constants.mainptr["end"] - f.tell()), "more bytes")
            # Change pointers
            for ptrgroup in ptrgroups:
                atstr = "@" + common.toHex(ptrgroup)
                for ptr in ptrgroups[ptrgroup]:
                    f.seek(ptr["pos"])
                    fin.seek(ptr["ptr"])
                    if ptr["data"]:
                        jpstr = game.readData(fin, allptrs)
                    else:
                        jpstr = game.readString(fin, invtable, allptrs)
                    if jpstr + atstr in translations:
                        jpstr = translations[jpstr + atstr]
                    elif jpstr in translations:
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
                        writegroups = "writegroups" in datptr and datptr["writegroups"]
                        usedictionary = "dictionary" in datptr and datptr["dictionary"]
                        wordwrap = "wordwrap" in datptr and datptr["wordwrap"] or 0
                        fin.seek(datptr["offset"])
                        if "end" in datptr:
                            while fin.tell() < datptr["end"]:
                                strstart = fin.tell()
                                jpstr = game.readString(fin, invtable)
                                fin.readZeros(binsize)
                                allstrings.append({"start": strstart, "end": fin.tell() - 1, "str": jpstr,
                                                   "writegroups": writegroups, "dictionary": usedictionary, "wordwrap": wordwrap})
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
                                allstrings.append({"start": strstart, "end": fin.tell() - 1, "str": jpstr,
                                                   "ptrpos": ptrs[i]["pos"], "writegroups": writegroups, "dictionary": usedictionary, "wordwrap": wordwrap})
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
                            if jpstr["wordwrap"] > 0:
                                jpstr["str"] = common.wordwrap(jpstr["str"], glyphs, jpstr["wordwrap"], game.detectTextCode, default=0xa)
                            if jpstr["str"].startswith("<<"):
                                jpstr["str"] = game.alignLeft(jpstr["str"][2:], glyphs)
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
                            common.logDebug("Writing pointer string", jpstr["str"], "at", common.toHex(f.tell()))
                            # Write the string and update the pointer
                            strpos = f.tell()
                            game.writeString(f, jpstr["str"], table, dictionary if jpstr["dictionary"] else {}, maxlen=maxpos - f.tell(), writegroups=jpstr["writegroups"])
                            f.writeUIntAt(jpstr["ptrpos"], strpos + 0x02000000)
                        else:
                            # Try to fit the string in the given space
                            f.seek(jpstr["start"])
                            common.logDebug("Writing fixed string", jpstr["str"], "at", common.toHex(f.tell()))
                            game.writeString(f, jpstr["str"], table, dictionary if jpstr["dictionary"] else {}, maxlen=jpstr["end"] - f.tell(), writegroups=jpstr["writegroups"])
                            while f.tell() < jpstr["end"]:
                                f.writeByte(0)
    common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))

    # Export font data, dictionary data and apply armips patch
    with common.Stream(fontdata, "wb") as f:
        for charcode in range(0x9010, 0x908f + 1):
            c = invtable[charcode]
            f.writeByte(glyphs[c].width)
    with codecs.open(dictionarydata, "w", "utf-8") as f:
        alldictionary = []
        for dictentry in dictionary:
            dictname = "DICTIONARY_" + common.toHex(dictionary[dictentry]).lower()
            dictvalue = dictname + ":\n" + game.writeDictionaryString(dictentry, table)
            f.write(".dw " + dictname + "\n")
            alldictionary.append(dictvalue)
        f.write("\n")
        f.write("\n".join(alldictionary))
        f.write("\n")
    common.armipsPatch(common.bundledFile("bin_patch.asm"))
