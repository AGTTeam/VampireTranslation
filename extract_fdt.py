import math
from hacktools import common
from PIL import Image


def run(data):
    infile = data + "extract_BMP/FDT/000.BIN"
    outfile = data + "font_output.png"

    common.logMessage("Extracting FDT to", outfile, "...")
    with common.Stream(infile, "rb", False) as f:
        width = f.readUShort()
        width = 8
        height = f.readUShort()
        charn = f.readUShort()
        charperline = 16
        charlines = math.ceil(charn / charperline)
        bytelen = (width * height) // 8
        imgwidth = (charperline * width) + charperline + 1
        imgheight = (charlines * height) + charlines + 1
        imgx = 1
        imgy = 1
        img = Image.new("RGB", (imgwidth, imgheight), (255, 0, 0))
        pixels = img.load()
        for i in range(charn):
            charx = imgx
            chary = imgy
            for j in range(bytelen):
                data = f.readByte()
                for x in range(8):
                    if data >> 7 & 1:
                        pixels[charx, chary] = (255, 255, 255)
                    else:
                        pixels[charx, chary] = (0, 0, 0)
                    data <<= 1
                    charx += 1
                    if charx - imgx == width:
                        charx = imgx
                        chary += 1
            imgx += width + 1
            if imgx == imgwidth:
                imgx = 1
                imgy += height + 1
        img.save(outfile, "PNG")
    common.logMessage("Done!")
