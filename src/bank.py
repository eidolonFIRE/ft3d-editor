from ctypes import *
from enums import *
from structs import *

class Bank():
    def __init__(self, index, struct=None):
        self.index = index
        self.channels = sorted([x for x in struct.channels if x != 0xffff]) if struct else []
        if len(self.channels) > 100:
            print("Error! Bank {} has too many channels! {} (max 100)".format(index, len(self.channels)))

    def __str__(self):
        return "{:2}) {}".format(self.index + 1, ", ".join([str(x) for x in self.channels]))
