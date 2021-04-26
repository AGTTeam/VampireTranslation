import math
import os
from hacktools import common, nitro
import constants


def readIMGData(f, paloff, tileoff, mapoff):
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
    if len(paloffs) > 2:
        common.logError("pal>2", len(paloffs))
    if len(tileoffs) > 2:
        common.logError("tile>2", len(tileoffs), len(mapoffs))
    return paloffs, tileoffs, mapoffs


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


def findPalette(file, infolder):
    basepath = file.split("/")[0] + "/"
    filenum = int(file.replace(".ANCG", "").replace(basepath, ""))
    # Search for the palette
    foundpal = ""
    nextfile = filenum + 1
    if file == "MG6/000.ANCG":
        nextfile += 1
    nextname = basepath + str(nextfile).zfill(3) + ".ANCL"
    if os.path.isfile(infolder + nextname):
        foundpal = nextname
    else:
        for i in range(filenum - 1, -1, -1):
            palname = basepath + str(i).zfill(3) + ".ANCL"
            if os.path.isfile(infolder + palname):
                foundpal = palname
                break
    return foundpal


def readANCGGraphics(f, file, infolder):
    foundpal = findPalette(file, infolder)
    if foundpal == "":
        common.logError("Palette not found for file", file)
        return None, None, None

    with common.Stream(infolder + foundpal, "rb") as fpal:
        palettes, bpp = readANCL(fpal, file)

    size = os.path.getsize(infolder + file)
    tiles = readANCG(f, size, bpp)
    foldername = file.split("/")[0]
    if file in constants.manualcells:
        cells = readCells(constants.manualcells[file])
    elif foldername in constants.manualcells:
        cells = readCells(constants.manualcells[foldername])
    else:
        cells = None
    return tiles, cells, palettes, bpp


def readANCL(f, file):
    palette = []
    f.seek(4)
    colornum = f.readUShort()
    bpp = f.readUShort()
    for j in range(colornum):
        palette.append(common.readPalette(f.readUShort()))
    indexedpalettes = {}
    indexedpalettes[0] = palette
    if "SMALL_CG" in file:
        bpp = 8
    return indexedpalettes, bpp


def readANCG(f, size, bpp):
    f.seek(8)
    ncgr = nitro.NCGR()
    ncgr.tiles = []
    ncgr.bpp = bpp
    ncgr.tilesize = 8
    ncgr.tileoffset = f.tell()
    tilelen = size - 8
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
        ncgr.width = numpix if numpix < 0x100 else 0x0100
        ncgr.height = int(numpix // ncgr.width)
        common.logDebug("Assuming size", ncgr.width, ncgr.height)
    common.logDebug("Finished reading file at", common.toHex(f.tell()))
    return ncgr


def readCells(manualcells):
    ncer = nitro.NCER()
    ncer.banks = []
    ncer.banknum = 0
    ncer.tbank = ncer.bankoffset = ncer.blocksize = ncer.partitionoffset = 0
    curroff = 0
    for manualbank in manualcells:
        repeat = int(manualbank["repeat"]) if "repeat" in manualbank else 1
        for i in range(repeat):
            bank = nitro.Bank()
            bank.cells = []
            ncer.banks.append(bank)
            ncer.banknum += 1
    i = 0
    banki = 0
    while i < ncer.banknum:
        manualbank = manualcells[banki]
        repeat = int(manualbank["repeat"]) if "repeat" in manualbank else 1
        for r in range(repeat):
            bank = ncer.banks[i]
            bank.cellnum = len(manualbank["cells"])
            bank.layernum = 1
            bank.partitionoffset = bank.width = bank.height = 0
            for j in range(len(manualbank["cells"])):
                manualcell = manualbank["cells"][j]
                cell = nitro.Cell()
                cell.objoffset = cell.layer = cell.objmode = cell.priority = 0
                cell.mosaic = cell.depth = cell.xflip = cell.yflip = cell.rsflag = False
                cell.width = manualcell["width"]
                cell.height = manualcell["height"]
                cell.pal = manualbank["pal"] if "pal" in manualbank else 0
                cell.x = manualcell["x"] if "x" in manualcell else 0
                cell.y = manualcell["y"] if "y" in manualcell else 0
                if cell.x + cell.width > bank.width:
                    bank.width = cell.x + cell.width
                if cell.y + cell.height > bank.height:
                    bank.height = cell.y + cell.height
                cell.numcell = j
                cell.tileoffset = curroff
                curroff += ((cell.width * cell.height) // (8 * 8))
                bank.cells.append(cell)
            common.logDebug(vars(bank))
            for cell in bank.cells:
                common.logDebug(vars(cell))
            i += 1
        banki += 1
    return ncer
