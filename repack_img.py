import os
from hacktools import common, nitro
import images


def run(data):
    infolder = data + "extract_BMP/"
    outfolder = data + "repack_BMP/"
    workfolder = data + "work_IMG/"

    common.logMessage("Repacking IMG from", workfolder, "...")
    files = common.getFiles(infolder, ".IMG")
    lastpals = []
    totfiles = 0
    for file in common.showProgress(files):
        dirname = os.path.dirname(file)
        if not os.path.isdir(workfolder + dirname):
            continue
        if file == "DATESL/002.IMG":
            continue
        with common.Stream(infolder + file, "rb") as fin:
            with common.Stream(outfolder + file, "wb") as f:
                common.logDebug("Repacking", file)
                # Read section offsets
                paloff = fin.readUInt() * 4
                tileoff = fin.readUInt() * 4
                mapoff = fin.readUInt() * 4
                common.logDebug("Sections:", common.toHex(paloff), common.toHex(tileoff), common.toHex(mapoff))
                # Read image
                paloffs, tileoffs, mapoffs = images.readIMGData(fin, paloff, tileoff, mapoff)
                if len(mapoffs) == 0 or len(mapoffs) > 2:
                    common.logError("Can't repack file", file)
                    fin.seek(0)
                    f.write(fin.read())
                    continue
                palettes, tiles, maps = images.readIMG(fin, paloffs, tileoffs, mapoffs)
                if len(paloffs) == 0:
                    common.logDebug("No palettes")
                    palettes = lastpals
                else:
                    lastpals = palettes
                # Copy file up until the first tile
                fin.seek(0)
                f.write(fin.read(tileoffs[0]))
                # Repack them
                newtileoffs = []
                mapfiles = []
                for i in range(len(mapoffs) - 1):
                    pngfile = workfolder + file.replace(".IMG", "_" + str(i).zfill(2) + ".png")
                    mapdata = common.Stream().__enter__()
                    if os.path.isfile(pngfile):
                        common.logDebug("Repacking", pngfile)
                        tiles[i].tileoffset = 0
                        maps[i].mapoffset = 0
                        open("temptile.bin", "w").close()
                        open("tempmap.bin", "w").close()
                        nitro.writeMappedNSCR("temptile.bin", "tempmap.bin", tiles[i], maps[i], pngfile, palettes, maps[i].width, maps[i].height, writelen=False)
                        with common.Stream("temptile.bin", "rb") as temptile:
                            f.write(temptile.read())
                            if f.tell() % 4 > 0:
                                f.writeZero(f.tell() % 4)
                            newtileoffs.append(f.tell())
                        with common.Stream("tempmap.bin", "rb") as tempmap:
                            mapdata.writeUShort(maps[i].width // 8)
                            mapdata.writeUShort(maps[i].height // 8)
                            mapdata.write(tempmap.read())
                            if mapdata.tell() % 4 > 0:
                                mapdata.writeZero(mapdata.tell() % 4)
                        os.remove("temptile.bin")
                        os.remove("tempmap.bin")
                        totfiles += 1
                    else:
                        common.logDebug("Copying", pngfile)
                        # Just copy the tile and map data
                        fin.seek(tileoffs[i])
                        f.write(fin.read(tileoffs[i+1] - fin.tell()))
                        newtileoffs.append(f.tell())
                        fin.seek(mapoffs[i])
                        mapdata.write(fin.read(mapoffs[i+1] - fin.tell()))
                    mapdata.seek(0)
                    mapfiles.append(mapdata)
                # Write the new map data
                newmapoffs = []
                mapoff = f.tell()
                f.writeUInt(len(mapfiles))
                for i in range(len(mapfiles)):
                    f.writeUInt(0)
                for mapdata in mapfiles:
                    f.write(mapdata.read())
                    newmapoffs.append(f.tell())
                f.seek(8)
                f.writeUInt(mapoff // 4)
                # Write the new offsets
                f.seek(tileoff + 4)
                for newtileoff in newtileoffs:
                    f.writeUInt((newtileoff - tileoff) // 4)
                f.seek(mapoff + 4)
                for newmapoff in newmapoffs:
                    f.writeUInt((newmapoff - mapoff) // 4)

    # Repack ANCG files
    files = common.getFiles(infolder, ".ANCG")
    open("tempcell.bin", "w").close()
    for file in common.showProgress(files):
        if file == "MANGA_LINE/000.ANCG":
            continue
        dirname = os.path.dirname(file)
        if not os.path.isdir(workfolder + dirname):
            continue
        pngfile = workfolder + file.replace(".ANCG", ".png")
        if not os.path.isfile(pngfile):
            continue
        common.copyFile(infolder + file, outfolder + file)
        with common.Stream(infolder + file, "rb") as fin:
            common.logDebug("Repacking", file)
            tiles, cells, palettes, bpp = images.readANCGGraphics(fin, file, infolder)
        if cells is None:
            continue
        nitro.writeNCER(outfolder + file, "tempcell.bin", tiles, cells, pngfile, palettes, checkRepeat=False, writelen=False, checkalpha=True)
        totfiles += 1
    os.remove("tempcell.bin")
    common.logMessage("Done! Repacked", totfiles, "files")
