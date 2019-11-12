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

    def __init__(self, title, h, w, y, x):
        self.coords = (h,w,y,x)
        self.win = curses.newwin(h,w,y,x)
        self.win.border()
        if title: self.win.addstr(0, 3, " %s " % title, COLOR["header"])
        self.win.refresh()
        self.scrollpos = 0
        self.hexoffset = 0
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

    def append(self, s, color="text"):
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
        for c in s:
            if self.hexoffset % 16 == 0:
                self.append(("\n" if self.hexoffset > 0 else "") +"%08X  " % self.hexoffset, "offset")
            cy, cx = self.pad.getyx()
            roff = self.hexoffset % 16
            self.pad.move(cy, 10 + roff * 3)
            self.pad.addstr("%02X" % c, COLOR[color])
            self.pad.move(cy, 60 + roff)
            self.pad.addstr(chr(c) if 31 < c < 127 else "·", COLOR[color])
            self.hexoffset += 1

class Input():
    """Our simple Input-Widget"""
    # TODO: Better input handling (←/→ navigate/insert)?

    def __init__(self, h, w, y, x):
        self.coords = (h, w, y, x)
        self.win = curses.newwin(h, w, y, x)
        self.win.border()
        self.inp = ""
        self.history = []
        self.shist = -1
        self.redraw()

    def redraw(self):
        self.win.addstr(1,1, " "*(self.coords[1]-2))
        self.win.addstr(1,1, self.inp)
        self.win.refresh()

    def clear(self):
        if self.inp and (len(self.history) == 0 or self.inp != self.history[0]):
            self.history.insert(0, self.inp)
        self.inp = ""
        self.shist = -1
        self.redraw()

    def append(self, c, hexmode=False):
        # boundry-check, "scroll" (well, trim left)
        if hexmode:
            c = "".join(filter(lambda h: h in '01234567890ABCDEF', c.upper()))
            if c and len(self.inp.replace(" ", "")) % 2: c += " "
        self.inp += c
        sw = self.coords[1]-3
        if len(self.inp) < sw:
            self.win.addstr(c)
        else:
            self.win.addstr(1,1, self.inp[-sw:])
        self.win.refresh()

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

    def backspace(self, hexmode=False):
        sw = self.coords[1]-3
        gc = 1
        if hexmode and self.inp[-1:] == " ": gc = 2
        self.inp = self.inp[:-gc]
        if len(self.inp) < sw:
            cy, cx = self.win.getyx()
            cx -= gc
            if cx < 1: cx = 1
            self.win.addstr(cy, cx, "  ")
            self.win.move(cy, cx)
        else:
            self.win.addstr(1, 1, self.inp[-sw:])

class Toggle():
    def __init__(self, win, y, x, key, choices, hint=None, current=0):
        self.win = win
        self.y, self.x = y, x
        self.key = key
        self.hint = hint
        self.choices = choices
        self.current = current
        self.smaxlen = max(map(len, self.choices))
        try: self.display()
        except: pass
        
    def nextState(self):
        self.current = (self.current + 1) % len(self.choices)
        self.display()
        
    def maxLen(self):
        return max(map(len, s))
        
    def display(self):
        cy, cx = self.win.getyx()
        self.win.addstr(self.y, self.x, " %s " % self.key, COLOR["key"])
        if self.hint: self.win.addstr("(%s) " % self.hint, COLOR["hint"])
        self.win.addstr(self.getState().center(self.smaxlen)+" ", COLOR["state"])
        self.win.move(cy, cx)
        self.win.refresh()
    
    def getState(self):
        return self.choices[self.current]

class Key():
    def __init__(self, win, y, x, key, text, action):
        self.win = win
        self.y, self.x = y, x
        self.key = key
        self.text = text
        self.action = action
        try: self.display()
        except: pass
        

    def display(self):
        cy, cx = self.win.getyx()
        self.win.addstr(self.y, self.x, " %s " % self.key, COLOR["key"])
        self.win.addstr(self.text+" ", COLOR["state"])
        self.win.move(cy, cx)
        self.win.refresh()

class Gui():
    HELP = """
        F1 : Show this help
        F2 : Pause/Unpause transmission                  [TODO]
        F4 : Clear Views / reset counter
        F5 : Toggle Input mode (Text/Hex/File)
        F6 : Toggle CR/LF after input on send (in Text-Mode)
        F7 : Toggle Codepage-translation (textview)
        F8 : Toggle display of input / output in hexdump
        
        F10: Quit

        PgUp/PgDn: Scroll ⅓ Page up/down
        Home/End : Scroll to top or bottom

        ↓/↑ : go through input-history (repeat command)
    \n"""

    def __init__(self):
        ay, ax = curses.LINES, curses.COLS
        assert ay >= 8, "Terminal must be at least 8 lines high"
        assert ax >= 80, "Terminal must be at least 80 lines wide"
        self.out_asc = TxtWin("", ay-3, ax//2, 0, 0)
        self.out_hex = TxtWin("Hexdump", ay-3, ax//2, 0, ax//2)
        self.in_str = Input(3, ax, ay-3, 0)
        self.n2brk = {"None":"", "LF":"\n", "CR": "\r", "CRLF": "\r\n", "0x00": "\0"}

        in_w = self.in_str.coords[1]
        hx_s = self.out_hex.coords
        self.keys = {
            curses.KEY_F1:  Key(self.in_str.win,  2,         in_w-24,    "F1",  "Help",         lambda: self.message(self.HELP)),
            curses.KEY_F4:  Key(self.out_hex.win, hx_s[0]-1, hx_s[1]-20, "F4",  "Clear Output", self.emptyView),
            curses.KEY_F10: Key(self.in_str.win,  2,         in_w-13,    "F10", "Quit",         self.quit)
        }
        
        as_s = self.out_asc.coords[1]
        self.tInp = Toggle(self.in_str.win,  2, 3,       "F5", ["Text", "Hex", "File"],      "Mode")
        self.tBrk = Toggle(self.in_str.win,  2, 22,      "F6", list(self.n2brk.keys()),      "Append")
        self.tAsc = Toggle(self.out_asc.win, 0, as_s-31, "F7", list(translate.PAGES.keys()), "Codepage")
        self.tHex = Toggle(self.out_hex.win, 0, 3,       "F8", ["Both", "Receive", "Send"],  "Show Stream")

        self.toggles = {
            curses.KEY_F5: self.tInp,
            curses.KEY_F6: self.tBrk,
            curses.KEY_F7: self.tAsc,
            curses.KEY_F8: self.tHex,
        }
        
        self.running = True

    def show(self, s, color): 
        # show stuff in both views and scroll to bottom. s may be (UTF-8) str oder bytearray
        # translate input for textview. always show everything there.
        #su = s.encode("UTF-8") if type(s) is str else s
        su = s.encode(self.tAsc.getState(), "ignore") if type(s) is str else s
        self.out_asc.append(translate.translate(su, self.tAsc.getState()), color)
        
        # selectively untouched hexdump
        th = self.tHex.getState()
        if th == "Both" or th+color in ("Receivetext", "Sendsend"):
            
            self.out_hex.appendHex(su, color)
        self.bscroll("end")

    def message(self, s): # show message with different color only in textview
        self.out_asc.append(s, "offset")
        self.out_asc.scroll("end")

    def error(self, s): # show error message with different color only in textview
        self.out_asc.append(s, "error")
        self.out_asc.scroll("end")

    def bscroll(self, s): # scroll both view
        self.out_asc.scroll(s)
        self.out_hex.scroll(s)

    def emptyView(self):
        self.out_asc.pad.erase()
        self.out_hex.pad.erase()
        self.out_hex.hexoffset = 0
        self.bscroll("end")
        
    def quit(self):
        self.running = False
