#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2017 Sebastian Bachmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import socket
import time
from struct import pack
from PIL import Image
import os
from itertools import chain
import sys
from colortemp import colortemp


def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return [(255 - pos * 3) & 0xFF, 0, (pos * 3) & 0xFF]
    elif pos < 170:
        pos -= 85
        return [0, (pos * 3) & 0xFF, (255 - pos * 3) & 0xff]
    else:
        pos -= 170
        return [(pos * 3) & 0xff, (255 - pos * 3) & 0xff, 0]


def rearange(buf):
    """
    Rearanges the buffer from an x,y image to the actual pixel position
    """

    # buf will be an bytearray with length x*y and contains tuple with 3 items

    # Need to put all columns from 8 to 15 at the end
    #
    # And swap every second line
    nbuf = []
    for c, i in enumerate(list(range(0, 256, 16)) + list(range(8, 256, 16))):
        line = buf[i:i + 8]
        if c % 2 == 1:
            line = line[::-1]
        nbuf += line

    return bytearray([item for sublist in nbuf for item in sublist])


def imageToBuffer(fname):
    im = Image.open(fname)
    pix = list(im.getdata())
    if len(pix[0]) == 4:
        pix = [(b,g,r) for r,g,b,a in pix]
    else:
        pix = [(b,g,r) for r,g,b in pix]

    if len(pix) != 256:
        return bytearray([0] * 768)

    return rearange(pix)


class ArtNet(object):
    def __init__(self, dst="255.255.255.255", port=0x1936, brightness=6, controlb=True):
        """
            Brightness: parameter from 0 to 8. 0 ...  always off, 8 ... full brightness
            controlb: if brightness should be controlled
        """
        self.seq = 0
        self.dst = dst
        self.port = port
        self.brightness = 8 - brightness
        self.controlb = controlb
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.universe = 3

        #                    Protocol name               DMX         Version   Seq   Phy
        self.hdr = bytearray(b'Art-Net\x00') + bytearray([0, 0x50] + [0, 14])

    def sendrgb(self, r, g, b):
        buf = bytearray([r, g, b, 0, 0] * 12)
        self.sock.sendto(self.hdr + pack(">B", self.seq) + b'\x00' + pack("<H", self.universe) + pack(">H", len(buf)) + buf, (self.dst, self.port))
        self.seq = (self.seq + 1) % 256


    def sendwa(self, w, a):
        buf = bytearray([0, 0, 0, a, w] * 12)
        self.sock.sendto(self.hdr + pack(">B", self.seq) + b'\x00' + pack("<H", self.universe) + pack(">H", len(buf)) + buf, (self.dst, self.port))
        self.seq = (self.seq + 1) % 256




if __name__ == "__main__":
    # NOTE: Artnet supports only 512 light values per universe.
    # Therefore we should in practise use two universes and parse the header...

    art = ArtNet(dst="10.20.255.255", controlb=False)

    art.sendrgb(255,255,255)
    time.sleep(1)
    art.sendrgb(0,255,255)
    time.sleep(1)
    art.sendrgb(0,0,255)
    time.sleep(1)
    art.sendrgb(0,255,0)
    time.sleep(1)
    art.sendrgb(255,0,0)
    time.sleep(1)

    art.sendwa(255,255)
    time.sleep(1)

    for i in range(255):
        art.sendwa(i, 0)

    for i in range(255):
        art.sendwa(0, i)
