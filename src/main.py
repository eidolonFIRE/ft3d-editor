#!/usr/bin/python3
from bank import Bank
from channel import Channel
from structs import Struct_File, Struct_Channel

import argparse
from ctypes import *



def calc_checksum(file):
    if isinstance(file, Struct_File):
        buf = (c_char * sizeof(file))()
        memmove(buf, byref(file), sizeof(file))
        return sum([ord(x) for x in buf])
    else:
        return sum(raw[:43000])


# ==============================================================================


if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(description='FT3d MEMORY.dat editor')
    parser.add_argument('input_file', nargs='?',
                        help='MEMORY.dat or .csv file', default='MEMORY.dat')
    parser.add_argument('-c', dest='csv', nargs='?', const=True,
                        help='Export CSV file')
    parser.add_argument('-d', dest='dat', nargs='?', const=True,
                        help='Export dat file')
    parser.add_argument('-p', dest='pad', nargs='?', const='1,0',
                        help='Pad csv number of COL,ROW')
    args = parser.parse_args()

    channels = None
    banks = None

    # ======= INPUT =======

    if ".dat" in args.input_file.lower():
        # ----- parse -----
        with open(args.input_file, "rb") as inFile:
            raw = inFile.read()
        data = cast(pointer(create_string_buffer(raw)), POINTER(Struct_File)).contents

        for i, v in enumerate(data.pad_m3):
            if v > 0 and v < 0xff:
                print(i, hex(v))

        print("checksum: {:04X}".format(data.checksum))

        _checksum = calc_checksum(raw)
        if data.checksum != _checksum:
            print("Checksum mismatch! Should be {}".format(_checksum))
        print("sum: {:04X}".format(_checksum))

        banks = [Bank(index, each) for index, each in enumerate(data.banks)]
        channels = [Channel(dat=(index, each, data.channel_flags[index], banks)) for index, each in enumerate(data.channels)]

    elif ".csv" in args.input_file.lower():
        with open(args.input_file, "r") as inFile:
            csv = inFile.read()
        channels = []
        pad = [int(x) for x in args.pad.split(",")] if args.pad else [0, 0]

        # Parse Channels
        prevIndex = 1
        for line in csv.split("\n")[pad[1]:]:
            csv = [x.strip() for x in line.split(",")[pad[0]:]]
            # If it's valid line, parse to Channel()
            # To be valid the first cell (index) is non-empty
            if len(csv[0]) and csv[0] is not "X":
                if csv[0] is "-":
                    csv[0] = prevIndex + 1
                channels.append(Channel(csv=csv))
                prevIndex = channels[-1].index

        # Assemble Banks
        banks = [Bank(x) for x in range(24)]
        for eachChan in channels:
            for bankIdx in eachChan.banks:
                banks[bankIdx].channels.append(eachChan.index)
        for each in banks:
            if len(each.channels) > 100:
                print("Error! Bank {} has too many channels! {} (max 100)".format(each.index, len(each.channels)))

    else:
        print("Unrecognized input file type: {}".format(args.input_file))


    # ======= OUTPUT =======

    # --- CSV FILE ---
    if args.csv and isinstance(args.csv, str):
        with open(args.csv, 'w') as csvOut:
            for ch in channels:
                if not ch.empty and ch.enabled:
                    csvOut.write(ch.to_csv() + "\n")

    # --- DAT FILE ---
    if args.dat and isinstance(args.dat, str):
        with open(args.dat, 'wb') as datOut:
            file = Struct_File()

            for ch in channels:
                idx = ch.index - 1
                if sum(file.channels[idx].name) > 0:
                    print("Error. Channel {} is already filled!".format(idx))
                    continue

                if not ch.empty:
                    # write channel entry
                    file.channels[idx] = ch.to_dat()
                    # write channel flag
                    file.channel_flags[idx] = (0x1 - ch.empty * 0x1) | ch.enabled * 0x2 | ch.skip * 0x4

            # blank the rest of the channels
            allChans = set([x.index - 1 for x in channels if not x.empty])
            print(allChans)
            for i in range(1100):
                if i not in allChans:
                    memset(byref(file.channels[i]), 0xff, sizeof(Struct_Channel))

            # fill bank lists
            for bk in banks:
                for idx, ch in enumerate(bk.channels):
                    file.banks[bk.index].channels[idx] = ch - 1
                # blank the rest
                file.banks[bk.index].channels[len(bk.channels):] = [0xffff] * (100 - len(bk.channels))

            # set the checksum
            file.checksum = calc_checksum(file)

            datOut.write(file)


    # --- PRINT TO CLI ---
    if channels:
        print("\n///// CHANNELS /////")
        for ch in channels:
            if not ch.empty and ch.enabled:
                if args.csv is not None:
                    print(ch.to_csv())
                else:
                    print(ch)

    if banks:
        print("\n///// BANKS /////")
        for each in banks:
            print(each)
