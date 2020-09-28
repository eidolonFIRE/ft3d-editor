from ctypes import BigEndianStructure, c_ubyte, c_char, c_ushort, c_uint

# ============ BIT-level breakdown of remaining data ============

# ---( optionsA )---
# [7-6] : ???
# [5]   : Wide/Narrow bandw
# [4]   : clock shift
# [3-0] : ???

# ---( unkown )---
# [15-0] : ???     ... could be related to modem? Has data for APRS station

# ---( dcs_pol )---
# [7-4] : ???
# [3-0] : dcs polarity

# ---( s_meter )---
# [7-4] : ???
# [3-0] : s_meter level

# ---( misc_options )---
# [7-6] : ???
# [5]   : attenuator enabled
# [4-1] : ???              ... something shows up for modem APRS station
# [0]   : bell enabled


class Struct_Channel(BigEndianStructure):  # size:32
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
                ("misc_options", c_ubyte)]


class Struct_Bank(BigEndianStructure):  # size:200
    _fields_ = [("channels", c_ushort * 100)]


class Struct_DGID(BigEndianStructure):  # size:2
    _fields_ = [("rx", c_ubyte),
                ("tx", c_ubyte)]


class Struct_File(BigEndianStructure):
    _fields_ = [("banks", Struct_Bank * 24),
                ("channel_flags", c_ubyte * 1100),
                ("pad_m2", c_ubyte * 244),
                ("channels", Struct_Channel * 1100),
                ("dgid", Struct_DGID * 900),  # 41600
                ("pad_m3", c_ubyte * 654),
                ("checksum", c_uint)]  # 43800
