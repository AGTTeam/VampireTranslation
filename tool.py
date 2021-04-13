import os
import click
from hacktools import common, nds
import game

version = "0.6.0"
data = "VampireData/"
romfile = data + "vampire.nds"
rompatch = data + "vampire_patched.nds"
headerfile = data + "extract/header.bin"
bannerfile = data + "repack/banner.bin"
patchfile = data + "patch.xdelta"
infolder = data + "extract/"
replacefolder = data + "replace/"
outfolder = data + "repack/"


@common.cli.command()
@click.option("--rom", is_flag=True, default=False)
@click.option("--bin", is_flag=True, default=False)
@click.option("--bmp", is_flag=True, default=False)
@click.option("--fdt", is_flag=True, default=False)
@click.option("--img", is_flag=True, default=False)
def extract(rom, bin, bmp, fdt, img):
    all = not rom and not bin and not bmp and not fdt and not img
    if all or rom:
        nds.extractRom(romfile, infolder, outfolder)
    if all or bin:
        import extract_bin
        extract_bin.run(data)
    if all or bmp:
        import extract_bmp
        extract_bmp.run(data)
    if all or fdt:
        import extract_fdt
        extract_fdt.run(data)
    if all or img:
        import extract_img
        extract_img.run(data)


@common.cli.command()
@click.option("--no-rom", is_flag=True, default=False)
@click.option("--bin", is_flag=True, default=False)
@click.option("--fdt", is_flag=True, default=False)
@click.option("--img", is_flag=True, default=False)
@click.option("--bmp", is_flag=True, default=False)
def repack(no_rom, bin, fdt, img, bmp):
    all = not bin and not fdt and not img and not bmp
    if all or bin:
        import repack_bin
        repack_bin.run(data)
    if all or fdt:
        import repack_fdt
        repack_fdt.run(data)
    if all or img:
        import repack_img
        repack_img.run(data)
    if all or bmp:
        import repack_bmp
        repack_bmp.run(data)

    if not no_rom:
        if os.path.isdir(replacefolder):
            common.mergeFolder(replacefolder, outfolder)
        nds.editBannerTitle(bannerfile, "Vampire Knight DS\n\nD3 Publisher")
        nds.repackRom(romfile, rompatch, outfolder, patchfile)


@common.cli.command()
@click.argument("text")
def translate(text):
    table, invtable = game.getTable(data)
    ret = ""
    group = 0
    for c in text:
        charcode = table[c]
        chargroup = charcode >> 8
        if group != chargroup:
            group = chargroup
            ret += common.toHex(group)
        ret += common.toHex(charcode & 0xff)
    common.logMessage(ret)


if __name__ == "__main__":
    click.echo("VampireTranslation version " + version)
    if not os.path.isdir(data):
        common.logError(data + " folder not found.")
        quit()
    common.runCLI(common.cli)
