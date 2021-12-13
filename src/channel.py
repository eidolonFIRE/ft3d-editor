from ctypes import *
from enums import *
from structs import *
import re


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
        self.unk_misc = (struct.misc_options >> 4) & 0x1
        self.clock_shift = ClockShift((struct.optionsA >> 4) & 0x1)
        self.bandw = Bandw((struct.optionsA >> 5) & 0x1)
        self.s_meter = struct.s_meter & 0xf
        self.squelch = bool(struct.s_meter >> 7)
        self.offset = self._parse_freq(struct.offset)
        self.charset = struct.charset
        self.banks = []
        self.rx_mode = RxMode.AM if (struct.step >> 6) & 0x1 else (RxMode.AUTO if ((struct.misc_options >> 3) & 0x1) else RxMode.FM)
        self.priority = False

        if banks is not None:
            for each in banks:
                self.banks.append(self.index - 1 in each.channels)

        if not self.empty:
            self.step = Step(struct.step & 0xf)
            self.tone = TONES[struct.tone]
            self.dcs = DCS_List[struct.dcs]
            self.dcs_pol = DCSPolarity((struct.dcs_pol >> 4) & 0xf)
            self.tone_mode = ToneMode(struct.tx & 0xf)
            self.offset_pol = OffsetPol((struct.step >> 4) & 0x3)
        else:
            self.step = Step(0)
            self.tone = TONES[0]
            self.dcs = DCS_List[0]
            self.dcs_pol = DCSPolarity(0)
            self.tone_mode = ToneMode(0)
            self.offset_pol = OffsetPol(0)

    def to_dat(self):
        chan = Struct_Channel()

        chan.optionsA = (self.clock_shift << 4) | (self.bandw << 5)
        if self.freq >= 30000:
            chan.optionsA |= 5
        elif self.freq >= 3000:
            chan.optionsA |= 4
        elif self.freq >= 300:
            chan.optionsA |= 3
        elif self.freq >= 30:
            chan.optionsA |= 2
        elif self.freq >= 3:
            chan.optionsA |= 1

        chan.step = (self.offset_pol << 4) | (self.step) | ((self.rx_mode == RxMode.AM) << 6)
        chan.freq = (c_ubyte * 3)(*self._pack_freq(self.freq))
        chan.tx = self.txpwr << 6 | self.mode << 4 | self.tone_mode
        chan.name = bytes([ord(x) for x in self.name] + [0xff] * (16 - len(self.name)))
        chan.offset = (c_ubyte * 3)(*self._pack_freq(self.offset))
        chan.tone = TONES.index(self.tone)
        chan.dcs = DCS_List.index(self.dcs)
        chan.dcs_pol = self.dcs_pol << 4
        chan.s_meter = self.s_meter | ((1 if self.squelch else 0) << 7)
        chan.misc_options = self.bell | self.attn << 5 | ((self.rx_mode == RxMode.AUTO) << 3) | (self.unk_misc << 4)
        if self.charset is not None:
            chan.charset = self.charset

        # this const seems to appears in every channel
        chan.dcs_pol |= 0xd

        return chan

    def _parse_csv(self, csv):
        # ===== parse from .csv table =====
        self.raw = None
        self.empty = False
        self.index = int(csv[0])
        self.priority = csv[1] == "ON"
        self.skip = csv[19] == "ON"
        self.step = Step[f"_{csv[21].strip('KHz').replace('.','_')}" if csv[21] else "_auto"]
        self.attn = csv[23] == "ON"
        self.bell = csv[25] == "ON"
        self.clock_shift = ClockShift.A if csv[27] == "OFF" else ClockShift.B
        self.name = csv[10]
        self.charset = (c_ubyte * 2)(*[0x00, 0x00])
        for x in re.finditer("(#[a-zA-Z])", csv[10]):
            i = x.span()[0]
            self.charset[i // 8] |= 0x1 << (7 - i%8)

        self.freq = round(float(csv[2]), 3)
        self.bandw = Bandw.Narrow if csv[26] == "ON" else Bandw.Wide
        self.squelch = csv[24] == "ON"
        self.txpwr = TxPwr[csv[18].split()[0]] if csv[18].startswith("L") else TxPwr.High
        self.offset = abs(round(float(csv[4]), 3)) if csv[4] else 0.0
        if csv[5] == "OFF":
            self.offset_pol = OffsetPol.OFF
        elif csv[5] == "+/-":
            self.offset_pol = OffsetPol.PLUS_MINUS
        elif csv[5].startswith("-"):
            self.offset_pol = OffsetPol.MINUS
        else:
            self.offset_pol = OffsetPol.PLUS

        # airband special case
        if 108.0 <= self.freq <= 137 or csv[7].upper() == "AM":
            self.mode = Mode.FM
            self.rx_mode = RxMode.AM
        else:
            self.mode = Mode[csv[8]]
            self.rx_mode = RxMode.AUTO if csv[6] == "ON" else RxMode.FM

        self.tone_mode = ToneMode[csv[11].replace(' ', '_') or "OFF"]
        self.tone = float(csv[12].split()[0]) if csv[12] else 100.0
        self.dcs = int(csv[13]) if csv[13] else DCS_List[0]
        self.dcs_pol = DCSPolarity[csv[14].replace(' ', '_')] if csv[14] else DCSPolarity(0)
        self.banks = [i for i, x in enumerate(csv[28:52]) if x.strip().upper() == "ON"]

        self.enabled = True
        self.s_meter = 0
        self.unk_misc = 1

    def to_csv(self):
        if self.offset_pol == OffsetPol.OFF:
            txfq = self.freq
            ofdr = "OFF"
        elif self.offset_pol == OffsetPol.PLUS_MINUS:
            txfq = 0.0
            ofdr = "+/-"
        elif self.offset_pol == OffsetPol.MINUS:
            txfq = self.freq - self.offset
            ofdr = "-RPT"
        else:
            txfq = self.freq + self.offset
            ofdr = "+RPT"
        if self.txpwr == TxPwr.L1:
            pwr = "L1 (0.1W)"
        elif self.txpwr == TxPwr.L2:
            pwr = "L2 (1W)"
        elif self.txpwr == TxPwr.L3:
            pwr = "L3 (2.5W)"
        else:
            pwr = "High (5W)"
        return "{idx:4},{priority},{rxfq:6.3f},{txfq:6.3f},{ofst:4.1f},{ofdr},{auto},{opmode},{mode},{tag},{name:16},{tnmd},{tone},{dcs:3},{dcs_pol},{usrtone},{rxdgid},{txdgid},{pwr},{skip},{autostep},{step},{mask},{attn},{smeter_sql},{bell},{bndw:1},{clock_shift},{banks},{comment},0".format(
            idx=self.index,
            priority="ON" if self.priority else "OFF",
            rxfq=self.freq,
            txfq=txfq,
            ofst=self.offset,
            ofdr=ofdr,
            auto="ON" if self.rx_mode == RxMode.AUTO else "OFF",
            opmode="AM" if self.rx_mode == RxMode.AM else "FM",
            mode=self.mode.name,
            tag="ON",
            name=self.name[:16],
            tnmd=self.tone_mode.name.replace('_', ' '),
            tone="{:5.1f} Hz".format(self.tone),
            dcs=self.dcs,
            dcs_pol=self.dcs_pol.name.replace('_', ' '),
            usrtone="1600 Hz",
            rxdgid="RX 00",
            txdgid="TX 00",
            pwr=pwr,
            skip="ON" if self.skip else "OFF",
            autostep="ON",
            step="AUTO" if self.step == Step._AUTO else f"{self.step.name[1:].replace('_','.')}KHz",
            mask="OFF",
            attn="ON" if self.attn else "OFF",
            smeter_sql="ON" if self.squelch else "OFF",
            bell="ON" if self.bell else "OFF",
            bndw="ON" if self.bandw is Bandw.Narrow else "OFF",
            clock_shift="ON" if self.clock_shift == ClockShift.B else "OFF",
            banks=",".join(["ON" if x else "OFF" for x in self.banks]),
            comment="",
            )

    def _parse_name(self, data):
        return ''.join([chr(i) for i in data]).rstrip('\x00').rstrip('\xff')

    def _parse_freq(self, data):
        return round((
            (data[0] >> 4) * 100 +
            (data[0] & 0xf) * 10 +
            (data[1] >> 4) +
            (data[1] & 0xf) / 10 +
            (data[2] >> 4) / 100 +
            (data[2] & 0xf) / 1000), 3)

    def _pack_freq(self, freq):
        return [(int(round(freq / 100,  5)) % 10 << 4 |
                 int(round(freq / 10,   4)) % 10),
                (int(round(freq,        3)) % 10 << 4 |
                 int(round(freq * 10,   2)) % 10),
                (int(round(freq * 100,  1)) % 10 << 4 |
                 int(round(freq * 1000, 0)) % 10)]

    def _channel_state(self):
        if not self.enabled:
            return "R"
        elif self.skip:
            return "S"
        else:
            return " "

    def __str__(self):
        return "{flag:1} {idx:4}) {name:16} | {rxfq:6.3f}mHz {bndw:3} step:{step:>5}kHz {ofst:>16} | {pwr} {mode:>3} {tnmd:4} {tone:>10} | DCS:{dcs:3} {dcs_pol:7} | {raw1:02x} {raw6:02x} {raw7:02x} {raw8:02x}".format(
            flag=self._channel_state(),
            idx =self.index,
            name=self.name,
            rxfq=self.freq,
            bndw="(N)" if self.bandw is Bandw.Narrow else "",
            step=self.step.name[1:].replace("_", "."),
            ofst="offset:{:4.1f}mHz".format(self.offset * (-1 if self.offset_pol is OffsetPol.MINUS else 1)) if self.offset_pol else "",
            pwr =self.txpwr.name,
            mode=RxMode.AM.name if self.rx_mode is RxMode.AM else self.mode.name,
            tnmd=self.tone_mode.name if self.tone_mode else "",
            tone="{:5.1f}mHz".format(self.tone) if self.tone_mode else "",
            dcs =self.dcs if self.tone_mode else "",
            dcs_pol=self.dcs_pol.name if self.tone_mode else "",
            raw1=self.raw.optionsA & 0xcf if self.raw else 0,
            raw6=self.raw.dcs_pol & 0xf0 if self.raw else 0,
            raw7=self.raw.s_meter & 0xf0 if self.raw else 0,
            raw8=self.raw.misc_options & 0xde if self.raw else 0,
            )
