from enum import IntEnum


class ClockShift(IntEnum):
    A = 0
    B = 1


class Bandw(IntEnum):
    Wide = 0
    Narrow = 1


class TxPwr(IntEnum):
    L1 = 0
    L2 = 1
    L3 = 2
    High = 3


class Mode(IntEnum):
    FM = 0
    AMS = 1  # auto mode select
    DN = 2  # digital
    VW = 3  # wide digital

class RxMode(IntEnum):
    AUTO = 0
    FM = 1
    AM = 2

class ToneMode(IntEnum):
    OFF = 0
    TONE = 1
    TONE_SQL = 2
    DCS = 3
    REV_TONE = 4
    PR_FREQ = 5
    PAGER = 6
    DC = 9
    T_D = 0xa
    D_T = 0xb


class DCSPolarity(IntEnum):
    RX_Normal_TX_Normal = 0
    RX_Invert_TX_Normal = 2
    RX_Both_TX_Normal   = 4
    RX_Normal_TX_Invert = 6
    RX_Invert_TX_Invert = 8
    RX_Both_TX_Invert   = 0xa


class Step(IntEnum):
    _AUTO  = 0
    _5_0   = 1
    _7_5   = 2
    _10_0  = 3
    _12_5  = 4
    _15_0  = 5
    _20_0  = 6
    _25_0  = 7
    _50_0  = 8
    _100_0 = 9


class OffsetPol(IntEnum):
    OFF = 0
    MINUS = 1
    PLUS = 2
    PLUS_MINUS = 3


TONES = [67, 69.3, 71.9, 74.4, 77, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4, 100.0, 103.5,
107.2, 110.9, 114.8, 118.8, 123, 127.3, 131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 159.8,
162.2, 165.5, 167.9, 171.3, 173.8, 177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6, 199.5,
203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8, 250.3, 254.1]

DCS_List = [23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72, 73, 74, 114, 115, 116,
122, 125, 131, 132, 134, 143, 145, 152, 155, 156, 162, 165, 172, 174, 205, 212, 223, 225,
226, 243, 244, 245, 246, 251, 252, 255, 261, 263, 265, 266, 271, 274, 306, 311, 315, 325,
331, 332, 343, 346, 351, 356, 364, 365, 371, 411, 412, 413, 423, 431, 432, 445, 446, 452,
454, 455, 462, 464, 465, 466, 503, 506, 516, 523, 526, 532, 546, 565, 606, 612, 624, 627,
631, 632, 654, 662, 664, 703, 712, 723, 731, 732, 734, 743, 754]
