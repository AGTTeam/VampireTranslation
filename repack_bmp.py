import os
from hacktools import common, compression
import game


def run(data):
    armfile = data + "extract/arm9.bin"
    infolder = data + "repack_BMP/"
    outfolder = data + "repack/data/bmp/"

    common.logMessage("Repacking BMP from", infolder, "...")
    repacked = 0
    with common.Stream(armfile, "rb+") as arm:
        offsets = game.getBMPOffsets(arm, outfolder)
        files = common.getFiles(outfolder, ".R00")
        for file in common.showProgress(files):
            if file != "FDT.R00":
                continue
            repacked += 1
            with common.Stream(outfolder + file, "wb", False) as f:
                common.logDebug("Repacking", file)
                offptr = offsets[file]
                folder = infolder + file.replace(".R00", "") + "/"
                i = 0
                for subfile in os.listdir(folder):
                    filepos = f.tell()
                    with common.Stream(folder + subfile, "rb") as fin:
                        uncdata = fin.read()
                        unclen = fin.tell()
                    f.writeUInt(unclen << 8)
                    f.seek(-1, 1)
                    cdata = compress(uncdata)
                    f.write(cdata)
                    arm.seek(offptr[i]["pos"])
                    arm.writeUInt(filepos)
                    arm.writeUInt(f.tell() - filepos - 3)
                    i += 1
        common.logMessage("Done! Repacked", repacked, "files")


def compress(indata):
    inlen = len(indata)
    out = bytearray(inlen)
    # Copy the first bytes
    firstcopy = 6
    out[0] = firstcopy - 1
    for i in range(firstcopy):
        out[i+1] = indata[i]
    readbytes = firstcopy
    complen = firstcopy + 1
    while readbytes < inlen:
        oldlength = min(readbytes, 0x400)
        length, disp = compression.getOccurrenceLength(indata, readbytes, min(inlen - readbytes, 0x22), readbytes - oldlength, oldlength, 1)
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
