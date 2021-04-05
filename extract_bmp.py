import os
from hacktools import common
import game


def run(data):
    infile = data + "extract/arm9.bin"
    infolder = data + "extract/data/bmp/"
    outfolder = data + "extract_BMP/"

    common.logMessage("Extracting BMP to", outfolder, "...")
    common.makeFolder(outfolder)
    with common.Stream(infile, "rb") as f:
        offsets = game.getBMPOffsets(f, infolder)
    files = common.getFiles(infolder, ".R00")
    for file in common.showProgress(files):
        # if file != "Flash_data.R00":
        #    continue
        size = os.path.getsize(infolder + file)
        with common.Stream(infolder + file, "rb", False) as f:
            common.logDebug("Extracting", file)
            folder = outfolder + file.replace(".R00", "") + "/"
            common.makeFolder(folder)
            try:
                decompress(f, offsets[file] if file in offsets else [], size, folder)
            except OSError:
                common.logError("OSError")
    common.logMessage("Done! Extracted", len(files), "files")


def decompress(f, offsets, size, out):
    i = 0
    hasoff = len(offsets) > 0
    seenptr = []
    for j in range(len(offsets) if hasoff else 99):
        if f.tell() >= size - 16:
            break
        if hasoff:
            offset = offsets[j]["offset"]
            if offset in seenptr:
                continue
            seenptr.append(offset)
            f.seek(offset)
            common.logDebug("Offset", common.toHex(offset), j)
        uncsize = f.readUInt() >> 8
        f.seek(-1, 1)
        if uncsize == 0x79a99a:
            # Skip a bugged size in GL_SM.R00 @ 0x3AC9C
            i += 1
            continue
        if uncsize == 0:
            common.logError("uncsize is", common.toHex(uncsize))
            break
        common.logDebug("uncsize", common.toHex(uncsize))
        filename = str(i).zfill(3) + ".BIN"
        magic = ""
        with common.Stream(out + filename, "wb+") as fout:
            while fout.tell() < uncsize and f.tell() < size:
                mask = f.readByte()
                if mask >> 7 == 0:
                    # If the last bit is not set, just copy mask+1 bytes
                    mask += 1
                    # common.logDebug("mask", mask)
                    fout.write(f.read(mask))
                else:
                    # Otherwise, take 5 bits + 3 as a count
                    # And the next byte + first 2 bits from the mask for the offset + 1
                    count = (mask >> 2) & 0x1f
                    count += 3
                    offset = f.readByte()
                    offset |= ((mask & 3) << 8)
                    offset += 1
                    # common.logDebug("count", common.toHex(count), "offset", common.toHex(offset), common.toHex(fout.tell()))
                    pos = fout.tell()
                    for j in range(count):
                        byte = fout.readByteAt(pos - offset + j)
                        fout.writeByte(byte)
            fout.seek(0)
            checkmagic = fout.readString(4)
            if len(checkmagic) == 4 and common.isAscii(checkmagic):
                magic = checkmagic
            else:
                fout.seek(0)
                paloff = fout.readUInt()
                tileoff = fout.readUInt()
                if (paloff == 0x3 and tileoff > 0) or (paloff == 0x0 and tileoff == 0x3):
                    magic = "IMG"
        common.logDebug("Finished at", common.toHex(f.tell()))
        if magic != "":
            os.rename(out + filename, out + filename.replace(".BIN", "." + magic))
        i += 1
