import codecs
import os
from hacktools import common, compression
import game


def run(data, testuncomp=False):
    armfilein = data + "extract/arm9.bin"
    armfileout = data + "repack/arm9.bin"
    oldfolder = data + "extract_BMP/"
    infolder = data + "repack_BMP/"
    outfolder = data + "repack/data/bmp/"

    if os.path.isfile(data + "bmpcache.txt"):
        with codecs.open(data + "bmpcache.txt", "r", "utf-8") as f:
            cache = common.getSection(f, "")
    else:
        cache = {}

    common.logMessage("Repacking BMP from", infolder, "...")
    repacked = 0
    with codecs.open(data + "bmpcache.txt", "w", "utf-8") as cachef:
        with common.Stream(armfilein, "rb") as arm:
            offsets = game.getBMPOffsets(arm, outfolder.replace("repack/", "extract/"))
        with common.Stream(armfileout, "rb+") as arm:
            files = common.getFiles(outfolder, ".R00")
            for file in common.showProgress(files):
                archive = file.replace(".R00", "")
                # Compare files
                newsubfolder = infolder + archive + "/"
                oldsubfolder = oldfolder + archive + "/"
                filediff = []
                skipfile = True
                for subfile in common.getFiles(newsubfolder):
                    subname = archive + "/" + subfile
                    newcrc = common.toHex(common.crcFile(newsubfolder + subfile), True)
                    oldcrc = common.toHex(common.crcFile(oldsubfolder + subfile), True)
                    if newcrc == oldcrc and subname not in cache:
                        common.logDebug("Skipping", subname, newcrc, oldcrc)
                        filediff.append(False)
                    else:
                        common.logDebug("Repacking", subname, newcrc, oldcrc)
                        filediff.append(True)
                        if skipfile and (subname not in cache or cache[subname][0] != newcrc):
                            common.logDebug("Not skipping file")
                            skipfile = False
                        cachef.write(subname + "=" + newcrc + "\n")
                # Repack if there's any difference
                if skipfile:
                    continue
                with common.Stream(outfolder.replace("repack/", "extract/") + file, "rb", False) as oldf:
                    with common.Stream(outfolder + file, "wb", False) as f:
                        common.logDebug("Repacking", file)
                        offptr = offsets[file]
                        folder = newsubfolder
                        i = 0
                        for subfile in common.getFiles(folder):
                            common.logDebug("Repacking subfile", subfile)
                            filepos = f.tell()
                            if filediff[i]:
                                with common.Stream(folder + subfile, "rb") as fin:
                                    uncdata = fin.read()
                                    unclen = fin.tell()
                                f.writeUInt(unclen << 8)
                                f.seek(-1, 1)
                                cdata = compress(uncdata)
                                f.write(cdata)
                                repacked += 1
                                if testuncomp:
                                    import extract_bmp
                                    testname = (folder + subfile).replace("/", "_") + "_test"
                                    with common.Stream(testname, "wb+") as testf:
                                        testf.write(cdata)
                                        testf.seek(0)
                                        extract_bmp.decompressData(testf, testname + "2", unclen, len(cdata))
                            else:
                                oldf.seek(offptr[i]["offset"])
                                f.write(oldf.read(offptr[i]["size"]))
                            if offptr[i]["pos"] > 0:
                                arm.seek(offptr[i]["pos"])
                                arm.writeUInt(filepos)
                                arm.writeUInt(f.tell() - filepos)
                            i += 1
    common.logMessage("Done! Repacked", repacked, "files")


def compress(indata):
    inlen = len(indata)
    out = bytearray(inlen * 2)
    # Copy the first bytes
    firstcopy = 6
    out[0] = firstcopy - 1
    for i in range(firstcopy):
        out[i+1] = indata[i]
    readbytes = firstcopy
    complen = firstcopy + 1
    while readbytes < inlen - 1:
        oldlength = min(readbytes, 0x400)
        length, disp = getOccurrenceLength(indata, readbytes, min(inlen - readbytes, 0x22), readbytes - oldlength, oldlength, 1)
        # Copy firstcopy bytes
        if length < 3:
            # common.logDebug("Copying bytes", common.toHex(complen), common.toHex(readbytes))
            out[complen] = firstcopy - 1
            complen += 1
            for i in range(min(inlen - readbytes, firstcopy)):
                out[complen] = indata[readbytes]
                readbytes += 1
                complen += 1
        else:
            # Copy length bytes from disp position
            offdisp = disp
            # common.logDebug("Writing mask", common.toHex(complen), common.toHex(readbytes), common.toHex(length), common.toHex(disp), common.toHex(offdisp))
            readbytes += length
            mask = (1 << 7)
            mask |= (((length - 3) & 0x1f) << 2)
            mask |= (((offdisp - 1) >> 8) & 3)
            offset = (offdisp - 1) & 0xff
            out[complen] = mask
            out[complen+1] = offset
            complen += 2
    return out[:complen]


def getOccurrenceLength(indata, newptr, newlength, oldptr, oldlength, mindisp=1):
    disp = 0
    if newlength == 0:
        return 0
    maxlength = 0
    # try every possible 'disp' value (disp = oldLength - i)
    for i in range(oldlength - mindisp):
        # work from the start of the old data to the end, to mimic the original implementation's behaviour
        # (and going from start to end or from end to start does not influence the compression ratio anyway)
        currentoldstart = oldptr + i
        currentlength = 0
        # determine the length we can copy if we go back (oldLength - i) bytes
        # always check the next 'newLength' bytes, and not just the available 'old' bytes,
        # as the copied data can also originate from what we're currently trying to compress.
        for j in range(newlength):
            # stop when the bytes are no longer the same
            if indata[currentoldstart + j] != indata[newptr + j]:
                break
            currentlength += 1
        # update the optimal value
        if currentlength > maxlength:
            maxlength = currentlength
            disp = oldlength - i
            # if we cannot do better anyway, stop trying.
            if maxlength == newlength:
                break
    return maxlength, disp
