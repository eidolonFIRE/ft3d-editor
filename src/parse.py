#!/usr/bin/python3

import argparse
from ctypes import *
from enum import IntEnum

class ClockShift(IntEnum):
    A = 0
    B = 1

class Bandw(IntEnum):
    Wide = 0
    Narrow = 1

class TxPwr(IntEnum):
    Low1 = 0
    Low2 = 1
    Low3 = 2
    High = 3

class Mode(IntEnum):
    FM = 0
    AMS = 1 # auto mode select
    DN = 2 # digital
    VW = 3 # wide digital

class ToneMode(IntEnum):
    Off = 0
    TN = 1
    TSQ = 2
    DCS = 3
    RTN = 4
    PR = 5
    PAG = 6
    DC = 9
    T_D = 0xa
    D_T = 0xb

class DCSPolarity(IntEnum):
    RxN_TxN = 0
    RxI_TxN = 2
    RxB_TxN = 4
    RxN_TxI = 6
    RxI_TxI = 8
    RxB_TxI = 0xa

class Step(IntEnum):
    _auto = 0
    _10_0 = 0x3
    _12_5 = 0x4
    _15_0 = 0x5
    _20_0 = 0x6
    _25_0 = 0x7
    _50_0 = 0x8
    _100_0 = 0x9

TONES = [67, 69.3, 71.9, 74.4, 77, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4, 100, 103.5,
107.2, 110.9, 114.8, 118.8, 123, 127.3, 131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 159.8,
162.2, 165.5, 167.9, 171.3, 173.8, 177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6, 199.5,
203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8, 250.3, 254.1,]

DCS_List = [23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72, 73, 74, 114, 115, 116, 
122, 125, 131, 132, 134, 143, 145, 152, 155, 156, 162, 165, 172, 174, 205, 212, 223, 225, 
226, 243, 244, 245, 246, 251, 252, 255, 261, 263, 265, 266, 271, 274, 306, 311, 315, 325, 
331, 332, 343, 346, 351, 356, 364, 365, 371, 411, 412, 413, 423, 431, 432, 445, 446, 452, 
454, 455, 462, 464, 465, 466, 503, 506, 516, 523, 526, 532, 546, 565, 606, 612, 624, 627, 
631, 632, 654, 662, 664, 703, 712, 723, 731, 732, 734, 743, 754,]


# ============ BIT-level breakdown of remaining data ============

# ---( opitionsA )---
# [7-6] : ???
# [5]   : Wide/Narrow bandw
# [4]   : clock shift
# [3-0] : ???

# ---( step )---
# [7-4] : ???
# [3-0] : step

# ---( unkown )---
# [15-0] : ???

# ---( dcs_pol )---
# [7-4] : ???
# [3-0] : dcs polarity

# ---( s_meter )---
# [7-4] : ???
# [3-0] : s_meter level

# ---( misc_options )---
# [7-6] : ???
# [5]   : attenuator enabled
# [4-1] : ???
# [0]   : bell enabled


class Struct_Channel(BigEndianStructure): # size:32
    _fields_ = [("optionsA", c_ubyte),
                ("step", c_ubyte),
                ("freq", c_ubyte * 3),
                ("tx", c_ubyte),
                ("unknown", c_ubyte * 2),
                ("name", c_char * 16),
                ("offset", c_ubyte * 3),
                ("tone", c_ubyte),
                ("dcs", c_ubyte),
                ("dcs_pol", c_ubyte),
                ("s_meter", c_ubyte),
                ("misc_options", c_ubyte)
            ]

class Struct_Bank(BigEndianStructure): # size:200
    _fields_ = [("channels", c_ushort * 100)]

class Struct_DGID(BigEndianStructure): # size:2
    _fields_ = [("rx", c_ubyte),
                ("tx", c_ubyte)]

class Struct_File(BigEndianStructure):
    _fields_ = [("banks", Struct_Bank * 24),
                ("channel_flags", c_ubyte * 1100),
                ("pad_m2", c_ubyte * 244),
                ("channels", Struct_Channel * 1100),
                ("dgid", Struct_DGID * 900), # 41600
                ("pad_m3", c_ubyte * 654),
                ("checksum", c_uint), # 43800
            ]



class Channel():
    def __init__(self, index, struct, flags):
        self.index = index
        self.raw = struct
        self.empty = (flags & 0x1) != 0x1
        self.enabled = (flags & 0x2) == 0x2 # (not removed)
        self.skip = (flags & 0x4) == 0x4
        self.name = self._parse_name(struct.name)
        self.freq = self._parse_freq(struct.freq)
        self.txpwr = TxPwr(struct.tx >> 6)
        self.mode = Mode((struct.tx >> 4) & 0x3)
        self.bell = struct.misc_options & 0x1
        self.attn = (struct.misc_options >> 5) & 0x1
        self.clock_shift = ClockShift((struct.optionsA >> 4) & 0x1)
        self.bandw = Bandw((struct.optionsA >> 5) & 0x1)
        self.s_meter = struct.s_meter & 0xf
        self.offset = self._parse_freq(struct.offset)

        if not self.empty:
            self.step = Step(struct.step & 0xf)
            self.tone = TONES[struct.tone]
            self.dcs = DCS_List[struct.dcs]
            self.dcs_pol = DCSPolarity((struct.dcs_pol >> 4) & 0xf)
            self.tone_mode = ToneMode(struct.tx & 0xf)
        else:
            self.step = Step(0)
            self.tone = TONES[0]
            self.dcs = DCS_List[0]
            self.dcs_pol = DCSPolarity(0)
            self.tone_mode = ToneMode(0)

    def _parse_name(self, data):
        return ''.join([chr(i) for i in data]).rstrip('\x00').rstrip('\xff')

    def _parse_freq(self, data):
        return (
            (data[0] >> 4) * 100 + 
            (data[0] & 0xf) * 10 +
            (data[1] >> 4) +
            (data[1] & 0xf) / 10 +
            (data[2] >> 4) / 100 +
            (data[2] & 0xf) / 1000)

    def _channel_state(self):
        if not self.enabled:
            return "R"
        elif self.skip:
            return "S"
        else:
            return " "

    def __str__(self):
        return "{flag:1} {idx:4}) {name:16} | {rxfq:6.3f}mHz {bndw:3} step:{step:>5}kHz  offset:{ofst:4.1f}mHz | {pwr} {mode:>3} {tnmd:3} {tone:5.1f}mHz | DCS:{dcs:3} {dcs_pol:7} | {raw1:02x} {raw2:02x} {raw4:02x}{raw5:02x} {raw6:02x} {raw7:02x} {raw8:02x}".format(
            flag=self._channel_state(),
            idx =self.index + 1,
            name=self.name,
            rxfq=self.freq,
            bndw="(N)" if self.bandw is Bandw.Narrow else "",
            step=self.step.name[1:].replace("_", "."),
            ofst=self.offset,
            pwr =self.txpwr.name,
            mode=self.mode.name,
            tnmd=self.tone_mode.name,
            tone=self.tone,
            dcs =self.dcs,
            dcs_pol=self.dcs_pol.name,
            raw1=self.raw.optionsA & 0xcf,
            raw2=self.raw.step & 0xf0,
            raw4=self.raw.unknown[0],
            raw5=self.raw.unknown[1],
            raw6=self.raw.dcs_pol & 0xf0,
            raw7=self.raw.s_meter & 0xf0,
            raw8=self.raw.misc_options & 0xde,
            )

class Bank():
    def __init__(self, index, struct):
        self.index = index
        self.channels = sorted([x for x in struct.channels if x != 0xffff])

    def __str__(self):
        return "{:2}) {}".format(self.index + 1, ", ".join([str(x) for x in self.channels]))


# ==============================================================================


if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(description='GPS log insights!')
    parser.add_argument('input_file', nargs='?',
                        help='MEMORY.dat', default='MEMORY.dat')
    # parser.add_argument('-g', dest='show_graph', action='store_true', default=False,
    #                     help='show graphs')
    # parser.add_argument('-s', metavar='amount', dest='smooth', nargs=1, type=int,
    #                     help='path smoothing factor (recommend 20)')
    # parser.add_argument('-f', dest='fix_alti', action='store_true', default=False)
    args = parser.parse_args()

    # ----- parse -----
    with open(args.input_file, "rb") as inFile:
        raw = inFile.read()
    data = cast(pointer(create_string_buffer(raw)), POINTER(Struct_File)).contents

    for i, v in enumerate(data.pad_m3):
        if v > 0 and v < 0xff:
            print(i, hex(v))

    print("checksum: {:04X}".format(data.checksum))

    print("sum: {:04X}".format(sum(raw[:43000])))


    # ----- print-----
    print("\n///// BANKS /////")
    banks = [Bank(index, each) for index, each in enumerate(data.banks)]
    for each in banks:
        print(each)

    print("\n///// CHANNELS /////")
    channels = [Channel(index, each, data.channel_flags[index]) for index, each in enumerate(data.channels)]
    for ch in channels:
        if not ch.empty:
            print(ch)
