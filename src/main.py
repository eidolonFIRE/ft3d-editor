#!/usr/bin/python3

import argparse
from ctypes import *
from enums import *
from structs import *


class Channel():
    def __init__(self, dat=None, csv=None):
        if dat is not None:
            # ===== parse from raw .dat data =====
            index, struct, flags, banks = dat
            self.index = index + 1
            self.raw = struct
            self.empty = (flags & 0x1) != 0x1
            self.enabled = (flags & 0x2) == 0x2  # (not removed)
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
            self.banks = []

            if banks is not None:
                for each in banks:
                    self.banks.append(self.index - 1 in each.channels)

            if not self.empty:
                self.step = Step(struct.step & 0xf)
                self.tone = TONES[struct.tone]
                self.dcs = DCS_List[struct.dcs]
                self.dcs_pol = DCSPolarity((struct.dcs_pol >> 4) & 0xf)
                self.tone_mode = ToneMode(struct.tx & 0xf)
                self.offset_pol = OffsetPol((struct.step >> 4) & 0xf)
            else:
                self.step = Step(0)
                self.tone = TONES[0]
                self.dcs = DCS_List[0]
                self.dcs_pol = DCSPolarity(0)
                self.tone_mode = ToneMode(0)
                self.offset_pol = OffsetPol(0)

        elif csv is not None:
            # ===== parse from .csv table =====
            self.raw = Struct_Channel()
            cells = [x.strip() for x in csv.split(",")]
            self.empty = False
            self.index = int(cells[0])
            self.skip = cells[1] is "S"
            self.enabled = cells[1] is not "R"
            self.name = cells[2]
            self.freq = float(cells[3])
            self.bandw = Bandw.Narrow if cells[4] is "N" else Bandw.Wide
            self.txpwr = TxPwr[cells[5]]
            self.offset = abs(float(cells[6]))
            self.offset_pol = (OffsetPol.MINUS if float(cells[6]) < 0 else OffsetPol.PLUS) if float(cells[6]) is not 0.0 else OffsetPol.NONE
            self.mode = Mode[cells[7]]
            self.tone_mode = ToneMode[cells[8]]
            self.tone = int(cells[9]) if cells[9] else 100
            self.dcs = int(cells[10]) if cells[10] else DCS_List[0]
            self.dcs_pol = DCSPolarity[cells[11]] if cells[11] else DCSPolarity(0)
            self.banks = [x.strip().upper() == "TRUE" for x in cells[12:]]

            self.bell = 0
            self.attn = 0
            self.clock_shift = 0
            self.step = Step(0)

        else:
            print("Channel is blank! Must provide either a csv or raw data!")

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

    def csv(self):
        return "{idx:4}, {flag:1}, {name:16}, {rxfq:6.3f}, {bndw:1}, {pwr}, {ofst:4.1f}, {mode:>3}, {tnmd:3}, {tone}, {dcs:3}, {dcs_pol:7},{banks},".format(
            idx =self.index,
            flag=self._channel_state(),
            name=self.name[:16],
            rxfq=self.freq,
            bndw="N" if self.bandw is Bandw.Narrow else "",
            ofst=self.offset * (-1 if self.offset_pol is OffsetPol.MINUS else 1),
            pwr =self.txpwr.name,
            mode=self.mode.name,
            tnmd=self.tone_mode.name,
            tone="{:5.1f}".format(self.tone) if self.tone_mode is not ToneMode.NONE else "",
            dcs =self.dcs if self.tone_mode is ToneMode.DCS else "",
            dcs_pol=self.dcs_pol.name if self.tone_mode is ToneMode.DCS else "",
            banks=",".join([" TRUE" if x else "FALSE" for x in self.banks])
            )

    def __str__(self):
        return "{flag:1} {idx:4}) {name:16} | {rxfq:6.3f}mHz {bndw:3} step:{step:>5}kHz  offset:{ofst:4.1f}mHz | {pwr} {mode:>3} {tnmd:3} {tone:5.1f}mHz | DCS:{dcs:3} {dcs_pol:7} | {raw1:02x} {raw4:02x}{raw5:02x} {raw6:02x} {raw7:02x} {raw8:02x}".format(
            flag=self._channel_state(),
            idx =self.index,
            name=self.name,
            rxfq=self.freq,
            bndw="N" if self.bandw is Bandw.Narrow else "",
            step=self.step.name[1:].replace("_", "."),
            ofst=self.offset * (-1 if self.offset_pol is OffsetPol.MINUS else 1),
            pwr =self.txpwr.name,
            mode=self.mode.name,
            tnmd=self.tone_mode.name,
            tone=self.tone,
            dcs =self.dcs,
            dcs_pol=self.dcs_pol.name,
            raw1=self.raw.optionsA & 0xcf,
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
    parser = argparse.ArgumentParser(description='FT3d MEMORY.dat editor')
    parser.add_argument('input_file', nargs='?',
                        help='MEMORY.dat or .csv file', default='MEMORY.dat')
    parser.add_argument('-c', dest='csv', action='store_true',
                        help='export CSV')
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

        # print("\n///// BANKS /////")
        banks = [Bank(index, each) for index, each in enumerate(data.banks)]
        # for each in banks:
        #     print(each)
        channels = [Channel(dat=(index, each, data.channel_flags[index], banks)) for index, each in enumerate(data.channels)]

    elif ".csv" in args.input_file.lower():
        with open(args.input_file, "r") as inFile:
            csv = inFile.read()
        channels = [Channel(csv=line) for line in csv.split("\n") if "," in line]


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
