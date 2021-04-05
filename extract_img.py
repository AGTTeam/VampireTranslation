import math
import os
from hacktools import common, nitro


def run(data):
    infolder = data + "extract_BMP/"
    outfolder = data + "out_IMG/"

    common.logMessage("Extracting IMG to", outfolder, "...")
    common.makeFolder(outfolder)
    files = common.getFiles(infolder, ".IMG")
    lastpals = []
    lastmaps = []
    for file in common.showProgress(files):
        with common.Stream(infolder + file, "rb") as f:
            common.logDebug("Extracting", file)
            # Read section offsets
            paloff = f.readUInt() * 4
            tileoff = f.readUInt() * 4
            mapoff = f.readUInt() * 4
            common.logDebug("Sections:", common.toHex(paloff), common.toHex(tileoff), common.toHex(mapoff))
            # Read palette offsets
            paloffs = []
            if paloff > 0:
                f.seek(paloff)
                paln = f.readUInt()
                for i in range(paln):
                    paloffs.append(paloff + f.readUInt() * 4)
                paloffs.insert(0, f.tell())
            common.logDebug("Palettes:", paloffs)
            # Read tile offsets
            tileoffs = []
            if tileoff > 0:
                f.seek(tileoff)
                tilen = f.readUInt()
                for i in range(tilen):
                    tileoffs.append(tileoff + f.readUInt() * 4)
                tileoffs.insert(0, f.tell())
            common.logDebug("Tiles:", tileoffs)
            # Read palette offsets
            mapoffs = []
            if mapoff > 0:
                f.seek(mapoff)
                mapn = f.readUInt()
                for i in range(mapn):
                    mapoffs.append(mapoff + f.readUInt() * 4)
                mapoffs.insert(0, f.tell())
            common.logDebug("Maps:", mapoffs)
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
            palettes, tiles, maps = readIMG(f, paloffs, tileoffs, mapoffs)
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
            else:
                for i in range(len(mapoffs) - 1):
                    common.logDebug("width", maps[i].width, "height", maps[i].height)
                    outfile = outfolder + file.replace(".IMG", "_" + str(i).zfill(2) + ".png")
                    nitro.drawNCGR(outfile, maps[i], tiles[0], palettes, maps[i].width, maps[i].height)
    common.logMessage("Done! Extracted", len(files), "files")


def readIMG(f, paloffs, tileoffs, mapoffs):
    palettes = readIMGPalettes(f, paloffs) if len(paloffs) > 0 else []
    bpp = 4 if 0 in palettes and len(palettes[0]) <= 16 else 8
    tiles = readIMGTiles(f, tileoffs, bpp)
    maps = readIMGMaps(f, mapoffs) if len(mapoffs) > 0 else []
    return palettes, tiles, maps


def readIMGPalettes(f, offsets):
    palettes = []
    for i in range(len(offsets) - 1):
        f.seek(offsets[i])
        pallen = offsets[i+1] - f.tell()
        palette = []
        for j in range(pallen // 2):
            palette.append(common.readPalette(f.readUShort()))
        palettes.append(palette)
    indexedpalettes = {}
    for i in range(len(palettes)):
        indexedpalettes[i] = palettes[i]
    return indexedpalettes


def readIMGTiles(f, offsets, bpp=8):
    tiles = []
    for i in range(len(offsets) - 1):
        f.seek(offsets[i])
        ncgr = nitro.NCGR()
        ncgr.tiles = []
        ncgr.bpp = bpp
        ncgr.tilesize = 8
        tilelen = offsets[i+1] - f.tell()
        tiledata = f.read(tilelen)
        for i in range(tilelen // (8 * ncgr.bpp)):
            singletile = []
            for j in range(ncgr.tilesize * ncgr.tilesize):
                x = i * (ncgr.tilesize * ncgr.tilesize) + j
                if ncgr.bpp == 4:
                    index = (tiledata[x // 2] >> ((x % 2) << 2)) & 0x0f
                else:
                    index = tiledata[x]
                singletile.append(index)
            ncgr.tiles.append(singletile)
        numpix = tilelen * 8 / ncgr.bpp
        root = int(math.sqrt(numpix))
        if math.pow(root, 2) == numpix:
            ncgr.width = ncgr.height = root
            common.logDebug("Assuming square size", ncgr.width)
        else:
            ncgr.width = int(numpix) if numpix < 0x100 else 0x0100
            ncgr.height = int(numpix // ncgr.width)
        tiles.append(ncgr)
    return tiles


def readIMGMaps(f, offsets):
    maps = []
    for i in range(len(offsets) - 1):
        f.seek(offsets[i])
        nscr = nitro.NSCR()
        nscr.maps = []
        nscr.width = f.readUShort() * 8
        nscr.height = f.readUShort() * 8
        for j in range((nscr.width // 8) * (nscr.height // 8)):
            map = nitro.readMapData(f.readUShort())
            nscr.maps.append(map)
        maps.append(nscr)
    return maps
