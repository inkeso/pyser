#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import translate

COLOR = {"header" : 0, "text" : 0, "send" : 0, "error": 0, "offset" : 0, "key":0, "hint":0, "state": 0}

class TxtWin(): 
    """Simple widget for displaying text and allowing for scroll"""
    # You can speed performance and perhaps reduce screen flicker by issuing
    # noutrefresh() calls on all windows, followed by a single curses.doupdate().
    
    PADSIZE = 2000
    hexModes = ["Both", "Receive", "Send"]
    
    def __init__(self, title, h, w, y, x):
        self.coords = (h,w,y,x) 
        self.win = curses.newwin(h,w,y,x)
        self.win.border()
        if title: self.win.addstr(0, 3, " %s " % title, COLOR["header"])
        self.win.refresh()
        self.scrollpos = 0
        self.hexoffset = 0
        self.inHex = 0
        self.inTranslate = 0
        self.trTabs = list(translate.PAGES.keys())
        self.pad = curses.newpad(self.PADSIZE, w-2)
        self.pad.move(0,0)
    
    def display(self):
        h,w,y,x = self.coords
        self.pad.refresh(self.scrollpos, 0, y+1, x+1, y+h-2, x+w-2)
    
    def scroll(self, pos="down"):
        lpos = self.pad.getyx()[0] - self.coords[0] + 3
        scrollins = self.coords[0] // 3 # ⅓ Screen
        if pos == "down": self.scrollpos += scrollins
        if pos == "up": self.scrollpos -= scrollins
        if pos == "home": self.scrollpos = 0
        if pos == "end": self.scrollpos = lpos 
        
        if self.scrollpos > lpos: self.scrollpos = lpos
        if self.scrollpos < 0: self.scrollpos = 0
        
        self.display()
    
    def nextTranslate(self):
        self.inTranslate = (self.inTranslate + 1) % len(self.trTabs)
        self.showTranslate()
        
    def showTranslate(self):
        self.win.addstr(0, self.coords[1] - 43, " F4 ", COLOR["key"])
        self.win.addstr("Clear ", COLOR["state"])

        self.win.addstr(0, self.coords[1] - 31, " F7 ", COLOR["key"])
        self.win.addstr("(Codepage) ", COLOR["hint"])
        self.win.addstr("%12s " % self.trTabs[self.inTranslate], COLOR["state"])
        self.win.refresh()

    def nextHex(self):
        self.inHex = (self.inHex + 1) % len(self.hexModes)
        self.showHex()
    
    def showHex(self):
        self.win.addstr(0, 3, " F8 ", COLOR["key"])
        self.win.addstr("(Show Stream) ", COLOR["hint"])
        self.win.addstr("%6s " % self.hexModes[self.inHex], COLOR["state"])
        self.win.refresh()
        
    def append(self, s, color="text"):
        # First of all: sanitize input
        s = translate.translate(s, self.trTabs[self.inTranslate])
        
        # check if pad has still enough space left.
        br = self.coords[1]-2
        nrows = sum([len(x) // br + 1 for x in s.split("\n")])
        cy, cx = self.pad.getyx()
        if (cy + nrows) >= self.PADSIZE: # uh-oh
            rem = nrows - (self.PADSIZE - cy) + 1 # remove just enough rows
            self.pad.move(0, 0)
            for i in range(rem): self.pad.deleteln()
            cy -= rem
            if cy < 0: # Ooops, buffer too small (see below)
                cy = 0
                cx = 0
            self.pad.move(cy, cx)
        
        try: # this may still explode if something bigger than buffer is comming in (unlikely)
            self.pad.addstr(s, COLOR[color])
        except curses.error:
            cy, cx = self.pad.getyx()
            self.pad.move(cy, 0)
            self.pad.addstr(" *** TRUNCATED *** ", COLOR["error"])
        
    def appendHex(self, s, color="text"):
        for c in s.encode():
            if self.hexoffset % 16 == 0:
                self.append(("\n" if self.hexoffset > 0 else "") +"%08X  " % self.hexoffset, "offset")
            cy, cx = self.pad.getyx()
            roff = self.hexoffset % 16
            self.pad.move(cy, 10 + roff * 3)
            self.pad.addstr("%02X" % c, COLOR[color])
            self.pad.move(cy, 60 + roff)
            # vielleicht, wenn translate "CP...", kann man dann doch...
            self.pad.addstr(chr(c) if 31 < c < 127 else "·", COLOR[color])
            self.hexoffset += 1

class Input():
    """Our simple Input-Widget"""

    stateStr = ["ASCII"] #, "Hex", "File"]
    breakStr = [["","None"], ["\n"," LF "], ["\r"," CR "], ["\r\n", "CRLF"], ["\0", "0x00"]]

    def __init__(self, h, w, y, x):
        self.coords = (h, w, y, x)
        self.win = curses.newwin(h, w, y, x)
        self.inp = ""
        self.inState = 0
        self.inBreak = 0
        self.history = []
        self.shist = -1
        self.redraw()
        
    def redraw(self):
        self.win.erase()
        self.win.border()
        self.win.addstr(1,1, self.inp)
        self.showState()

    def clear(self):
        if self.inp and (len(self.history) == 0 or self.inp != self.history[0]):
            self.history.insert(0, self.inp)
        self.inp = ""
        self.shist = -1
        self.redraw()
    
    def append(self, c):
        try:
            self.inp += c
            self.win.addstr(c)
            self.win.refresh()
        except curses.error:
            pass # ¯\_(ツ)_/¯

    def goHistory(self, delta=1):
        if len(self.history) == 0: return
        self.shist += delta
        if self.shist < 0:
            self.shist = -1
            self.inp = ""
        else:
            if self.shist >= len(self.history):
                self.shist = len(self.history) - 1
            self.inp = self.history[self.shist]
        self.redraw()

    def backspace(self):
        self.inp = self.inp[:-1]
        cy, cx = self.win.getyx()
        cx -= 1
        if cx < 1: cx = 1
        self.win.addstr(cy, cx," ")
        self.win.move(cy, cx)
    
    def nextBreak(self):
        self.inBreak = (self.inBreak + 1) % len(self.breakStr)
        self.showState()

    def nextState(self):
        self.inState = (self.inState + 1) % len(self.stateStr)
        self.showState()
    
    def showState(self):
        cy, cx = self.win.getyx()
        w = self.coords[1]
        self.win.addstr(2, 3, " F5 ", COLOR["key"])
        self.win.addstr("(Mode) ", COLOR["hint"])
        self.win.addstr("%5s " % self.stateStr[self.inState], COLOR["state"])
        self.win.addstr(2, 22, " F6 ", COLOR["key"])
        self.win.addstr("(Append) ", COLOR["hint"])
        self.win.addstr("%4s " % self.breakStr[self.inBreak][1], COLOR["state"])
        
        self.win.addstr(2, 22, " F6 ", COLOR["key"])
        self.win.addstr("(Append) ", COLOR["hint"])
        self.win.addstr("%4s " % self.breakStr[self.inBreak][1], COLOR["state"])
        
        self.win.addstr(2, w-24, " F1 ", COLOR["key"])
        self.win.addstr("Help ", COLOR["state"])
        self.win.addstr(2, w-13, " F10 ", COLOR["key"])
        self.win.addstr("Quit ", COLOR["state"])
        
        self.win.move(cy, cx)
        self.win.refresh()
    
    def getInput(self):
        return self.inp + self.breakStr[self.inBreak][0]
    
    def getBytes(self):
        # obacht bei höherwertigem UTF-8!
        return bytes([ord(x) for x in self.getInput()])
        
