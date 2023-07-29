import codecs
import os
from hacktools import common
import game
import constants


def run(data, analyze=False, writepos=False):
    infile = data + "extract/arm9.bin"
    outfile = data + "bin_output.txt"
    datfile = data + "dat_output.txt"
    binsize = os.path.getsize(infile)
    table, invtable = game.getTable(data)

    if analyze:
        allmain = []
        for i in range(constants.mainptr["offset"], constants.mainptr["end"] + 1):
            allmain.append(i)

    with common.Stream(infile, "rb") as f:
        common.logMessage("Extracting BIN to", outfile, "...")
        ptrgroups, allptrs = game.getBINPointerGroups(f)
        with codecs.open(outfile, "w", "utf8") as bin:
            seen = []
            seenptr = []
            for ptrgroup in common.showProgress(ptrgroups):
                firstwrite = True
                for ptr in ptrgroups[ptrgroup]:
                    if type(ptr) is list:
                        continue
                    f.seek(ptr["ptr"])
                    strstart = f.tell()
                    common.logDebug(common.toHex(strstart))
                    if ptr["data"]:
                        jpstr = game.readData(f, allptrs)
                    else:
                        jpstr = game.readString(f, invtable, allptrs)
                    strend = f.tell()
                    if analyze:
                        analyzeSpace(strstart, strend, seenptr, allmain)
                    if jpstr not in seen:
                        if firstwrite:
                            firstwrite = False
                            bin.write("\n# " + common.toHex(ptrgroup, True) + "\n")
                        seen.append(jpstr)
                        if writepos:
                            bin.write("#" + common.toHex(strstart, True) + "\n")
                        bin.write(jpstr + "=\n")
        common.logMessage("Done!")
        common.logMessage("Extracting DAT to", datfile, "...")
        with codecs.open(datfile, "w", "utf8") as dat:
            for file in common.showProgress(constants.datptrs):
                maindatptr = constants.datptrs[file]
                if type(maindatptr) is not list and "main" in maindatptr:
                    continue
                dat.write("\n!FILE:" + file + "\n")
                datoffsets = []
                if type(maindatptr) is list:
                    for subdatptr in maindatptr:
                        datoffsets.append(subdatptr)
                else:
                    datoffsets.append(maindatptr)
                for datptr in datoffsets:
                    f.seek(datptr["offset"])
                    if "end" in datptr:
                        while f.tell() < datptr["end"]:
                            strstart = f.tell()
                            jpstr = game.readString(f, invtable)
                            strend = f.tell()
                            dat.write(jpstr + "=\n")
                            f.readZeros(binsize)
                            if analyze:
                                analyzeSpace(strstart, strend, seenptr, allmain)
                    else:
                        ptrs = []
                        for i in range(datptr["count"]):
                            ptrs.append(f.readUInt() - 0x02000000)
                            if "skip" in datptr:
                                f.seek(datptr["skip"], 1)
                        for i in range(datptr["count"]):
                            f.seek(ptrs[i])
                            strstart = f.tell()
                            jpstr = game.readString(f, invtable)
                            if strstart >= constants.mainptr["offset"] and strstart <= constants.mainptr["end"]:
                                common.logMessage(file, common.toHex(strstart), jpstr)
                            strend = f.tell()
                            dat.write(jpstr + "=\n")
                            f.readZeros(binsize)
                            if analyze:
                                analyzeSpace(strstart, strend, seenptr, allmain)
        common.logMessage("Done!")
        if analyze:
            for i in allmain:
                common.logDebug(common.toHex(i))


def analyzeSpace(strstart, strend, seenptr, allmain):
    if strstart not in seenptr:
        seenptr.append(strstart)
        for i in range(strstart, strend + 1):
            if i in allmain:
                allmain.remove(i)
