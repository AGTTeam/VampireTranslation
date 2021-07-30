import os
from hacktools import common, nitro
import images


def run(data):
    infolder = data + "extract_BMP/"
    outfolder = data + "out_IMG/"

    common.logMessage("Extracting IMG to", outfolder, "...")
    common.makeFolder(outfolder)
    files = common.getFiles(infolder, ".IMG")
    lastpals = []
    lastmaps = []
    totfiles = 0
    for file in common.showProgress(files):
        with common.Stream(infolder + file, "rb") as f:
            common.logDebug("Extracting", file)
            # Read section offsets
            paloff = f.readUInt() * 4
            tileoff = f.readUInt() * 4
            mapoff = f.readUInt() * 4
            common.logDebug("Sections:", common.toHex(paloff), common.toHex(tileoff), common.toHex(mapoff))
            # Read offsets
            paloffs, tileoffs, mapoffs = images.readIMGData(f, paloff, tileoff, mapoff)
            # Check
            if len(tileoffs) == 0:
                common.logError("No tiles")
                break
            if len(paloffs) > 2:
                common.logError("pal>2", len(paloffs))
                break
            if len(tileoffs) > 2:
                common.logError("tile>2", len(tileoffs), len(mapoffs))
                break
            # Read image
            palettes, tiles, maps = images.readIMG(f, paloffs, tileoffs, mapoffs)
            if len(paloffs) == 0:
                common.logDebug("No palettes")
                palettes = lastpals
            else:
                lastpals = palettes
            if len(mapoffs) > 0:
                lastmaps = maps
            # Export them
            common.makeFolders(outfolder + os.path.dirname(file))
            if len(mapoffs) == 0:
                for i in range(len(tileoffs) - 1):
                    tilelen = len(tiles[i].tiles)
                    common.logDebug("No maps", tilelen)
                    if tilelen == 19:
                        width = lastmaps[0].width
                        height = lastmaps[0].height
                    elif tilelen == 6:
                        width = lastmaps[1].width
                        height = lastmaps[1].height
                    else:
                        width = tiles[i].width
                        height = tiles[i].height
                        common.logWarning("Unknown tilelen with 0 maps", tilelen, width, height)
                    outfile = outfolder + file.replace(".IMG", "_" + str(i).zfill(2) + ".png")
                    nitro.drawNCGR(outfile, None, tiles[i], palettes, width, height)
                    totfiles += 1
            else:
                for i in range(len(mapoffs) - 1):
                    common.logDebug("width", maps[i].width, "height", maps[i].height)
                    outfile = outfolder + file.replace(".IMG", "_" + str(i).zfill(2) + ".png")
                    nitro.drawNCGR(outfile, maps[i], tiles[0], palettes, maps[i].width, maps[i].height)
                    totfiles += 1
    files = common.getFiles(infolder, ".ANCG")
    for file in common.showProgress(files):
        if file == "MANGA_LINE/000.ANCG":
            continue
        with common.Stream(infolder + file, "rb") as f:
            common.logDebug("Extracting", file)
            tiles, cells, palettes, bpp = images.readANCGGraphics(f, file, infolder)

            common.makeFolders(outfolder + os.path.dirname(file))
            outfile = outfolder + file.replace(".ANCG", ".png")
            if cells is None:
                nitro.drawNCGR(outfile, None, tiles, palettes, tiles.width, tiles.height)
            else:
                nitro.drawNCER(outfile, cells, tiles, palettes)
            totfiles += 1
    common.logMessage("Done! Extracted", totfiles, "files")
