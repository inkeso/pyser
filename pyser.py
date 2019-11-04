#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Full featured serial console but with a fancy ncurses-TUI.

# Funktionen für Eingabe:
# - Byteweise sofort abschicken. ASCII 32-127 per Tastatur, anderes irgendwie anders....?
# - Linebuffered mit GNU readline inkl. History. Zeilenende umschaltbar CR, CRLF, LF oder nix.
# - Optional gesendete Befehle ins Log zu schreiben (andersfarbig)
# - Input-History!
# Funktionen für Ausgabe:
# - Optional unverändert in Datei schreiben (selbes für eingabe)
# - links Klartext; nicht-Ascii-bytes >128 durch CP437, <32 durch UTF-8 darstellen
# - rechts Hexdump. Farbig. 16 byte pro Zeile. Kodierung wie oben. Input ggf auch anders hervorheben


import re
import curses
import serial

# https://docs.python.org/3/howto/curses.html
# https://docs.python.org/3/library/curses.html

# CONFIG (TODO: getopts)
DEVICE = "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"
BAUD = 9600
PADSIZE = 12 # number of lines to keep in scrollback-pad
RECDUMP = "/dev/null" # record Received bytes to a file
SNDDUMP = "/dev/null" # record Sent bytes to a file

DBG=open("/tmp/pyser_dbg.log","w")
def dbglog(s):
    DBG.write(s)
    DBG.flush()


class sWin(): 
    """Simple widget for displaying text and allowing for scroll"""
    # You can speed performance and perhaps reduce screen flicker by issuing
    # noutrefresh() calls on all windows, followed by a single curses.doupdate().
    
    def __init__(self, title, h, w, y, x):
        self.coords = (h,w,y,x) 
        self.title = title
        self.win = curses.newwin(h,w,y,x)
        self.win.border()
        self.win.addstr(0, 3, " %s " % self.title, curses.color_pair(1) + curses.A_BOLD)
        self.win.refresh()
        self.pad = curses.newpad(PADSIZE, w-2)
        self.pad.move(0,0)
        self.scrollpos = 0
    
    def display(self):
        h,w,y,x = self.coords
        self.pad.refresh(self.scrollpos, 0, y+1, x+1, y+h-2, x+w-2)
    
    def scroll(self, pos="down"):
        lpos = self.pad.getyx()[0] - self.coords[0] + 3
        if pos == "down": self.scrollpos += 1
        if pos == "up": self.scrollpos -= 1
        if pos == "home": self.scrollpos = 0
        if pos == "end": self.scrollpos = lpos 
        
        if self.scrollpos > lpos: self.scrollpos = lpos
        if self.scrollpos < 0: self.scrollpos = 0
        
        self.display()
    
    def append(self, s, send=False):
        # First of all: check if pad has still enough space left.
        br = self.coords[1]-2
        nrows = sum([len(x) // br + 1 for x in s.split("\n")])
        cy, cx = self.pad.getyx()
        if (cy + nrows) >= PADSIZE: # uh-oh
            rem = nrows - (PADSIZE - cy) + 1 # remove just enough rows
            self.pad.move(0, 0)
            for i in range(rem): self.pad.deleteln()
            cy -= rem
            if cy < 0: # Ooops, buffer too small (see below)
                cy = 0
                cx = 0
            self.pad.move(cy, cx)
        
        try: # this may still explode if something bigger than buffer is comming in (unlikely)
            self.pad.addstr(s, curses.color_pair(2+send))
        except curses.error:
            cy, cx = self.pad.getyx()
            self.pad.move(cy, 0)
            self.pad.addstr(" *** TRUNCATED *** ", curses.color_pair(4)+curses.A_BOLD)
        self.scroll("end")
        self.display()


lips = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris."


def main(scr):
    scr.clear()
    scr.nodelay(True)
    scr.getch()
    
    # Styles
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE) # header
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK) # Received data
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK) # Sent data
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK) # ERROR
    
    # We can determine the size of the screen by using the curses.LINES and curses.COLS variables
    # let's create two windows for display stuff from DEVICE (ASCII and HEX)
    out_asc = sWin("Received / Sent (Text)", 25, 80, 0, 0)
    out_hex = sWin("Received / Sent (Hex)", 25, 80, 0, 80)
    
    out_asc.append("Begrüßed den PySer! (Vörsion Null, ganz ohne Kleider)\n\n")

    # and now wait for some input in a box
    # i'd like to have readline-functionality...
    in_str = curses.newwin(3,80,25,0)
    in_str.border()
    in_str.move(1,1)
    in_str.refresh()
    inp = ""

    dbg = curses.newwin(3,80,25,80)
    dbg.border()
    dbg.move(1,1)
    dbg.refresh()
    
    def debug(s):
        dbg.erase()
        dbg.border()
        dbg.addstr(1,1,s)
        dbg.refresh()

    # Prepare Serial Port
    try:
        ser = serial.Serial(DEVICE, BAUD)
        ser.timeout=.05
    except serial.SerialException as e:
        ser = None
        out_asc.append("CONNECTION FAILED\n", send=True)
        out_asc.append(str(e))

    sereadcount = 0
    while True:
        in_str.refresh()
        c = scr.getch()

        # TODO: Inputhandling kann so nich bleiben. aber erstmal langts.
        # Also je nach Modus wäre ja GNU readline geil...
        if c == -1: # no input
            if ser:
                rx = ser.read()
                while ser.inWaiting() > 0: rx += ser.read(ser.inWaiting())
                if len(rx) > 0: 
                    data = "".join(chr(x) for x in rx)
                    out_asc.append(data.replace("\r",""), send=False)
                    in_str.refresh()
                    sereadcount += 1
        
        elif 31 < c < 127: # ASCII
            inp += chr(c)
            in_str.addstr(1,1, inp)
        
        elif c == 10: # ENTER
            out_asc.append(inp+"\n", send=True)
            # currently without newline
            if ser: ser.write(bytes([ord(x) for x in inp]))
            inp = ""
            in_str.erase()
            in_str.border()
            in_str.move(1,1)
        
        elif c == curses.KEY_F11: # FUN: insert lorem ipsum (test, no write to ser)
            out_asc.append(lips, send=True)
            out_asc.scroll("end")
            out_hex.scroll("end")
        
        elif c == curses.KEY_NPAGE: # SCROLL
            out_asc.scroll("down")
            out_hex.scroll("down")
            
        elif c == curses.KEY_PPAGE:
            out_asc.scroll("up")
            out_hex.scroll("up")
        
        elif c == curses.KEY_HOME:
            out_asc.scroll("home")
            out_hex.scroll("home")

        elif c == curses.KEY_END:
            out_asc.scroll("end")
            out_hex.scroll("end")

        #else:
        #    debug("unknown Key: "+str(c))
        
        debug("serreads: "+str(sereadcount))
        
        #foo = in_str.getstr().decode()
        #out_asc.append(foo+"\n")
        #out_hex.append(" ".join([hex(ord(x)) for x in foo]))
        
curses.wrapper(main)

