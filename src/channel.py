from ctypes import *
from enums import *
from structs import *


class Channel():
    def __init__(self, dat=None, csv=None):
        if dat is not None:
            self._parse_dat(dat)
        elif csv is not None:
            self._parse_csv(csv)
        else:
            print("No Channel data. Must provide either csv or raw data!")

    def _parse_dat(self, dat):
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

    def _parse_csv(self, csv):
        # ===== parse from .csv table =====
        self.raw = Struct_Channel()
        self.empty = False
        self.index = int(csv[0])
        self.skip = csv[1] is "S"
        self.enabled = csv[1] is not "R"
        self.name = csv[2]
        self.freq = float(csv[3])
        self.bandw = Bandw.Narrow if "N" in csv[4] else Bandw.Wide
        self.txpwr = TxPwr[csv[5]]
        if csv[6]:
            self.offset = abs(float(csv[6]))
            self.offset_pol = (OffsetPol.MINUS if float(csv[6]) < 0 else OffsetPol.PLUS) if float(csv[6]) is not 0.0 else OffsetPol.NONE
        else:
            self.offset = 0.0
            self.offset_pol = OffsetPol.NONE
        self.mode = Mode[csv[7]]
        self.tone_mode = ToneMode[csv[8] or "NONE"]
        self.tone = float(csv[9]) if csv[9] else 100.0
        self.dcs = int(csv[10]) if csv[10] else DCS_List[0]
        self.dcs_pol = DCSPolarity[csv[11]] if csv[11] else DCSPolarity(0)
        self.banks = [i for i, x in enumerate(csv[12:36]) if x.strip().upper() == "TRUE"]

        self.bell = 0
        self.attn = 0
        self.clock_shift = 0
        self.step = Step(0)

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
            ofst=(self.offset * (-1 if self.offset_pol is OffsetPol.MINUS else 1)) if self.offset_pol > 0 else 0.0,
            pwr =self.txpwr.name,
            mode=self.mode.name,
            tnmd=self.tone_mode.name if self.tone_mode else "",
            tone="{:5.1f}".format(self.tone) if self.tone_mode else "",
            dcs =self.dcs if self.tone_mode is ToneMode.DCS else "",
            dcs_pol=self.dcs_pol.name if self.tone_mode is ToneMode.DCS else "",
            banks=",".join([" TRUE" if x else "FALSE" for x in self.banks])
            )

    def __str__(self):
        return "{flag:1} {idx:4}) {name:16} | {rxfq:6.3f}mHz {bndw:3} step:{step:>5}kHz {ofst:>16} | {pwr} {mode:>3} {tnmd:4} {tone:>10} | DCS:{dcs:3} {dcs_pol:7} | {raw1:02x} {raw4:02x}{raw5:02x} {raw6:02x} {raw7:02x} {raw8:02x}".format(
            flag=self._channel_state(),
            idx =self.index,
            name=self.name,
            rxfq=self.freq,
            bndw="(N)" if self.bandw is Bandw.Narrow else "",
            step=self.step.name[1:].replace("_", "."),
            ofst="offset:{:4.1f}mHz".format(self.offset * (-1 if self.offset_pol is OffsetPol.MINUS else 1)) if self.offset_pol else "",
            pwr =self.txpwr.name,
            mode=self.mode.name,
            tnmd=self.tone_mode.name if self.tone_mode else "",
            tone="{:5.1f}mHz".format(self.tone) if self.tone_mode else "",
            dcs =self.dcs if self.tone_mode else "",
            dcs_pol=self.dcs_pol.name if self.tone_mode else "",
            raw1=self.raw.optionsA & 0xcf,
            raw4=self.raw.unknown[0],
            raw5=self.raw.unknown[1],
            raw6=self.raw.dcs_pol & 0xf0,
            raw7=self.raw.s_meter & 0xf0,
            raw8=self.raw.misc_options & 0xde,
            )
