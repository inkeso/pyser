#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, random, hashlib

words = ["adipisicing", "aliqua", "amet", "anim", "aute", "cillum", "commodo", 
"consectetur", "consequat", "cupidatat", "deserunt", "doeiusmod", "dolor", 
"dolore", "Duis", "ea", "elit", "enimad", "esse", "est", "et", "eu", "ex", 
"Excepteur", "exercitation", "fugiat", "id", "in", "incididunt", "inculpa", 
"inreprehenderit", "ipsum", "irure", "labore", "laboris", "laborum", "Lorem", 
"magna", "minim", "mollit", "nisi", "non", "nostrud", "nullapariatur", 
"occaecat", "officia", "proident", "qui", "quis", "sed", "sint", "sit", "sunt", 
"tempor", "ullamco", "ut", "utaliquip", "velit", "veniam", "voluptate"]


# dummy serial device. randomly send bytes, react to input
class Serial():
    def __init__ (self, port=None, baudrate=9600, bytesize=8, parity='N', stopbits=1,
                  xonxoff=False, rtscts=False, dsrdtr=False,
                  timeout=None, write_timeout=None, inter_byte_timeout=None,
                  exclusive=None, **kwargs):
        self.timeout = timeout
        self.buffer = b"SERIAL DUMMY MODE. I'll answer with sha256 of your input.\r\n"
        self.lastfix=int(time.time())
    
    def read(self, n=0):
        if int(time.time()) % 60 == 0 and self.lastfix != int(time.time()):
            zefix = " ".join(random.sample(words,3)).title() + "! "
            self.buffer += (zefix + time.asctime() + "\r\n").encode()
            self.lastfix = int(time.time())
        
        s = self.buffer
        if self.buffer: 
            self.buffer = b''
        else:
            time.sleep(self.timeout)
        return s

    def inWaiting(self):
        return len(self.buffer)
    
    def write(self, s):
        self.buffer += hashlib.sha512(s).digest()

class SerialException(Exception): pass
