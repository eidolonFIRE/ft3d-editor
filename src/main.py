#!/usr/bin/python3
from bank import Bank
from channel import Channel
import argparse
from ctypes import *




# ==============================================================================


if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(description='FT3d MEMORY.dat editor')
    parser.add_argument('input_file', nargs='?',
                        help='MEMORY.dat or .csv file', default='MEMORY.dat')
    parser.add_argument('-c', dest='csv', action='store_true',
                        help='Export CSV')
    parser.add_argument('-p', dest='pad', nargs=1, default='1,1',
                        help='Pad csv number of COL,ROW')
    args = parser.parse_args()

    channels = None

    if ".dat" in args.input_file.lower():
        # ----- parse -----
        with open(args.input_file, "rb") as inFile:
            raw = inFile.read()
        data = cast(pointer(create_string_buffer(raw)), POINTER(Struct_File)).contents

        for i, v in enumerate(data.pad_m3):
            if v > 0 and v < 0xff:
                print(i, hex(v))

        print("checksum: {:04X}".format(data.checksum))

        _checksum = sum(raw[:43000])
        if data.checksum != _checksum:
            print("Checksum mismatch! Should be {}".format(_checksum))
        print("sum: {:04X}".format(_checksum))

        banks = [Bank(index, each) for index, each in enumerate(data.banks)]
        channels = [Channel(dat=(index, each, data.channel_flags[index], banks)) for index, each in enumerate(data.channels)]

    elif ".csv" in args.input_file.lower():
        with open(args.input_file, "r") as inFile:
            csv = inFile.read()
        channels = []
        pad = [int(x) for x in args.pad[0].split(",")] if args.pad else [0, 0]

        # Parse Channels
        for line in csv.split("\n")[pad[1]:]:
            csv = [x.strip() for x in line.split(",")]
            # If it's valid line, parse to Channel()
            # To be valid the first cell (index) is non-empty
            if len(csv[pad[0]]):
                channels.append(Channel(csv=csv[pad[0]:]))

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


    if channels:
        print("\n///// CHANNELS /////")
        for ch in channels:
            if not ch.empty and ch.enabled:
                if args.csv:
                    print(ch.csv())
                else:
                    print(ch)

    if banks:
        print("\n///// BANKS /////")
        for each in banks:
            print(each)
