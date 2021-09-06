import codecs
import os
from collections import OrderedDict
from hacktools import common
import constants


def readString(f, invtable, ptrs=None):
    # Strings are "compressed" by skipping the first byte
    # if it's the same as the previous character
    group = 0
    ret = ""
    while True:
        byte = f.readByte()
        if ptrs is None and byte == 0:
            break
        if byte >= 0x90 and byte <= 0xa5:
            group = byte
        elif byte == 0xa:
            ret += "|"
        elif byte < 0xa:
            ret += "<" + common.toHex(byte) + ">"
            if ptrs is not None:
                while True:
                    if f.tell() in ptrs:
                        return formatString(ret)
                    foundcode = False
                    for stringcode in constants.stringcodes:
                        if ret[-len(stringcode):] == stringcode:
                            foundcode = True
                            break
                    if foundcode:
                        break
                    byte = f.readByte()
                    ret += "<" + common.toHex(byte) + ">"
        else:
            charcode = (group * 0x100) + byte
            if charcode not in invtable:
                common.logWarning("Charcode", common.toHex(charcode), "not found")
                ret += "<" + common.toHex(group) + ">"
                ret += "<" + common.toHex(byte) + ">"
                group = 0
            else:
                ret += invtable[charcode]
    return formatString(ret)


def readData(f, ptrs):
    byte = f.readByte()
    ret = "<" + common.toHex(byte) + ">"
    while f.tell() not in ptrs:
        byte = f.readByte()
        ret += "<" + common.toHex(byte) + ">"
    return ret


def formatString(str):
    while str.endswith("<00>"):
        str = str[:-4]
    for stringcode in constants.stringcodes:
        str = str.replace(stringcode, constants.stringcodes[stringcode])
    return str


text_stats_dict_overhead = 0
text_stats_dict_saved = 0
text_stats_groups = 0
text_stats_other = 0
text_stats_compression_saving = 0


def writeString(f, s, table, dictionary={}, maxlen=-1, writegroups=False, compress=False):
    global text_stats_dict_overhead, text_stats_dict_saved, text_stats_groups, text_stats_other, text_stats_compression_saving
    s = s.replace("<ch1>", "<ch1>_")
    s = s.replace("<ch2>", "<ch2>_")
    s = s.replace("<ch3>", "<ch3>_")
    group = 0
    totlen = 0
    for stringcode in constants.stringcodes:
        s = s.replace(constants.stringcodes[stringcode], stringcode)
    x = 0
    # Write the string to a temporary memory stream
    tf = common.Stream().__enter__()
    while x < len(s):
        if not writegroups:
            # Loop the dictionary entries to find if we can match one
            for dictentry in dictionary:
                check = s[x:x+len(dictentry)]
                if check == dictentry:
                    addlen = 2
                    if group != 0x90:
                        addlen += 1
                    if maxlen != -1 and totlen + addlen > maxlen:
                        common.logError("String", s, "is too long (" + str(x) + "/" + str(len(s)) + ")")
                        break
                    if addlen > 2:
                        tf.writeByte(0x90)
                        text_stats_dict_overhead += 1
                    tf.writeByte(0x1)
                    tf.writeByte(dictionary[dictentry])
                    text_stats_dict_overhead += 2
                    text_stats_dict_saved += len(dictentry)
                    totlen += addlen
                    x += len(dictentry)
                    continue
        c = s[x]
        x += 1
        if c == "|":
            if maxlen != -1 and totlen + 1 > maxlen:
                common.logError("String", s, "is too long (" + str(x) + "/" + str(len(s)) + ")")
                break
            tf.writeByte(0xa)
            totlen += 1
        elif c == "_":
            group = 0
        elif c == "<":
            if maxlen != -1 and totlen + 1 > maxlen:
                common.logError("String", s, "is too long (" + str(x) + "/" + str(len(s)) + ")")
                break
            code = s[x] + s[x+1]
            tf.write(bytes.fromhex(code))
            x += 3
            totlen += 1
        else:
            if c not in table:
                common.logError("Character", c, "not found for string", s)
            else:
                charcode = table[c][0]
                if len(table[c]) > 1 and group > 0:
                    # Pick the best one
                    for ci in range(1, len(table[c])):
                        checkgroup = table[c][ci] >> 8
                        if checkgroup == group:
                            charcode = table[c][ci]
                            break
                chargroup = charcode >> 8
                if group != chargroup or writegroups:
                    if maxlen != -1 and totlen + 2 > maxlen:
                        common.logError("String", s, "is too long (" + str(x) + "/" + str(len(s)) + ")")
                        break
                    group = chargroup
                    tf.writeByte(group)
                    text_stats_groups += 1
                    tf.writeByte(charcode & 0xff)
                    text_stats_other += 1
                    totlen += 2
                else:
                    if maxlen != -1 and totlen + 1 > maxlen:
                        common.logError("String", s, "is too long (" + str(x) + "/" + str(len(s)) + ")")
                        break
                    tf.writeByte(charcode & 0xff)
                    text_stats_other += 1
                    totlen += 1
    stringlen = tf.tell()
    tf.seek(0)
    if not compress or "<" in s:
        f.write(tf.read())
        f.writeByte(0)
        return
    # Check how much we can save with compression
    stringbytes = tf.read()
    tf.seek(0)
    f.writeByte(stringbytes[0])
    x = 0
    while x < stringlen:
        saving = 0
        f.seek(-65530, 1)
        checkbytes = f.read(65530)
        for i in range(stringlen - x):
            # Grab a piece
            searchfor = stringbytes[x:stringlen - x - i]
            if len(searchfor) > 127 or len(searchfor) < 5 or searchfor[len(searchfor)-1] == 0x1:
                continue
            # Search for it
            foundat = checkbytes.find(searchfor)
            if foundat >= 0:
                text_stats_compression_saving += len(searchfor) - 4
                saving = len(searchfor)
                # common.logMessage("Writing at ", f.tell(), " for bytes ", searchfor)
                f.writeByte(0x1)
                f.writeByte(saving | (1 << 7))
                f.writeUShort(65530 + 4 - foundat)
                break
        if saving > 0:
            x += saving
        else:
            f.writeByte(stringbytes[x])
            x += 1
            if x < stringlen and stringbytes[x-1] == 0x1:
                f.writeByte(stringbytes[x])
                x += 1
    f.writeByte(0)


def writeDictionaryString(s, table):
    ret = []
    x = 0
    group = 0x90
    while x < len(s):
        c = s[x]
        x += 1
        if c == 0xa:
            ret.append(".db 0xa")
        else:
            charcode = table[c][0]
            chargroup = charcode >> 8
            if group != chargroup:
                group = chargroup
                ret.append(".db 0x" + common.toHex(group).lower())
            ret.append(".db 0x" + common.toHex(charcode & 0xff).lower())
    if group != 0x90:
        ret.append(".db 0x90")
    ret.append(".db 0x0")
    return " :: ".join(ret)


def alignLeft(s, glyphs, totlen=0x78):
    strlen = 0
    for c in s:
        strlen += glyphs[c].length if "c" in glyphs else 6
    maxlen = len(constants.alignglyphs) - 1
    while strlen < totlen:
        if totlen - strlen >= maxlen:
            s += constants.alignglyphs[maxlen]
            strlen += maxlen
        else:
            s += constants.alignglyphs[totlen - strlen]
            strlen = totlen
    return s


def alignCenter(s, glyphs, align=6):
    strlen = 0
    for c in s:
        strlen += glyphs[c].length if "c" in glyphs else 6
    remainder = strlen % align
    if remainder == 0:
        return s
    if remainder == 1:
        return constants.alignglyphs[3] + s + constants.alignglyphs[2]
    if remainder == 2:
        return constants.alignglyphs[2] + s + constants.alignglyphs[2]
    if remainder == 3:
        return constants.alignglyphs[2] + s + constants.alignglyphs[1]
    if remainder == 4:
        return constants.alignglyphs[1] + s + constants.alignglyphs[1]
    return constants.alignglyphs[1] + s


def alignCenterSpace(s, glyphs, align=108):
    strlen = 0
    for c in s:
        strlen += glyphs[c].length if "c" in glyphs else 6
    remainder = (align - strlen) // 6 // 2
    if remainder > 0:
        spacing = constants.alignglyphs[6]
        if remainder == 2:
            spacing = constants.alignglyphs[12]
        elif remainder == 3:
            spacing += constants.alignglyphs[12]
        elif remainder == 4:
            spacing = constants.alignglyphs[12] + constants.alignglyphs[12]
        s = spacing + s + spacing
    return s


def detectTextCode(s, i=0):
    if s[i] == "<":
        return len(s[i:].split(">", 1)[0]) + 1
    return 0


def getBINPointerGroups(f):
    datoffsets = []
    # Initialize allptr with the end of the last string
    allptrs = [0x13a3f4]
    datagroups = []
    allptrs.append(constants.mainptr["end"])
    ptrgroups = OrderedDict()
    for datptr in constants.datptrs:
        if type(constants.datptrs[datptr]) is list:
            for subdatptr in constants.datptrs[datptr]:
                datoffsets.append(subdatptr["offset"])
        else:
            offset = constants.datptrs[datptr]["offset"]
            datoffsets.append(offset)
            if "main" in constants.datptrs[datptr]:
                ptrgroups[offset] = []
            if "dataonly" in constants.datptrs[datptr]:
                datagroups.append(offset)
    f.seek(0xb12a8)
    while f.tell() < 0xb2810:
        ptrgroups[f.readUInt() - 0x02000000] = []
    for ptrgroup in ptrgroups:
        first = True
        f.seek(ptrgroup)
        datagroup = ptrgroup in datagroups
        while True:
            # Stop if we reach another ptr group
            if not first and (f.tell() in ptrgroups or f.tell() in datoffsets):
                break
            first = False
            ptrpos = f.tell()
            ptr = f.readUInt() - 0x02000000
            # Stop if we reach something that's not a pointer
            if ptr < 0 or ptr > 0x1d8000:
                break
            # Skip if the ptr is outside the main area
            if ptr < constants.mainptr["offset"] or ptr > constants.mainptr["end"]:
                continue
            allptrs.append(ptr)
            ptrgroups[ptrgroup].append({"pos": ptrpos, "ptr": ptr, "data": datagroup})
    return ptrgroups, allptrs


def getBMPOffsets(f, folder):
    ptrs = {}
    for file in constants.bmpptr:
        ptr = constants.bmpptr[file]
        ptrs[file] = []
        if type(ptr) is list:
            for offset in ptr:
                ptrs[file].append({"pos": 0, "size": 0, "offset": offset})
            continue
        f.seek(ptr)
        lastoff = -1
        filesize = os.path.getsize(folder + file)
        while True:
            offpos = f.tell()
            off = f.readUInt()
            size = f.readUInt()
            if off < lastoff or off > filesize:
                break
            if off < lastoff:
                continue
            lastoff = off
            ptrs[file].append({"pos": offpos, "size": size, "offset": off})
    return ptrs


def getTable(data):
    table = {}
    invtable = {}
    if not os.path.isfile(data + "table.txt"):
        common.logError("table.txt file not found")
        return table, invtable
    with codecs.open(data + "table.txt", "r", "utf-8") as tablef:
        section = common.getSection(tablef, "", comment="##")
    for code in section:
        glyph = section[code][0]
        glyph = glyph.replace("<3D>", "=")
        codehex = int(code, 16)
        if glyph not in table:
            table[glyph] = []
        table[glyph].append(codehex)
        invtable[codehex] = glyph
    return table, invtable


def getGlyphs(data):
    glyphs = {}
    dictionary = {}
    if not os.path.isfile(data + "fontconfig.txt"):
        common.logError("fontconfig.txt file not found")
        return glyphs
    dicti = 0xb
    with codecs.open(data + "fontconfig.txt", "r", "utf-8") as f:
        fontconfig = common.getSection(f, "", comment="##")
        for c in fontconfig:
            charlen = 0 if fontconfig[c][0] == "" else int(fontconfig[c][0])
            c = c.replace("<3D>", "=")
            if charlen == 0:
                dictionary[c] = dicti
                dicti += 1
            else:
                glyphs[c] = common.FontGlyph(0, charlen, charlen)
    return glyphs, dictionary
