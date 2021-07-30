import os
from hacktools import common
from PIL import Image


def run(data):
    infile = data + "extract_BMP/FDT/000.BIN"
    outfile = data + "repack_BMP/FDT/000.BIN"
    imgfiles = [data + "font_input.png", data + "font_input2.png"]

    common.logMessage("Repacking FDT from", imgfiles[0], "...")
    common.copyFile(infile, outfile)
    with common.Stream(outfile, "rb+", False) as f:
        for fntnum in range(len(imgfiles)):
            imgfile = imgfiles[fntnum]
            if not os.path.isfile(imgfile):
                common.logError("Input file", imgfile, "not found")
                return
            img = Image.open(imgfile)
            img = img.convert("RGB")
            pixels = img.load()
            width = f.readUShort()
            width = 8 if fntnum == 0 else 16
            height = f.readUShort()
            charn = f.readUShort()
            charperline = 16
            bytelen = (width * height) // 8
            imgwidth = (charperline * width) + charperline + 1
            imgx = 1
            imgy = 1
            for i in range(charn):
                charx = imgx
                chary = imgy
                for j in range(bytelen):
                    data = 0
                    for x in range(8):
                        if pixels[charx, chary] == (255, 255, 255):
                            data |= 1 << (7 - x)
                        charx += 1
                        if charx - imgx == width:
                            charx = imgx
                            chary += 1
                    f.writeByte(data)
                imgx += width + 1
                if imgx == imgwidth:
                    imgx = 1
                    imgy += height + 1
    common.logMessage("Done!")
