#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Full featured serial console like cuteterm, but with a fancy ncurses-TUI.

# TODO:
# - Parameter via getopt
# - In/Out in Datei schreiben (kombiniert, einzeln)
# - doku/readme

import re
import curses
import serial
#import serdummy as serial
import widgets
import translate
# https://docs.python.org/3/howto/curses.html
# https://docs.python.org/3/library/curses.html

DEVICE = "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"
BAUD = 9600
widgets.TxtWin.PADSIZE = 2000 # number of lines to keep in scrollback-pad
RECDUMP = "/dev/null" # record Received bytes to a file
SNDDUMP = "/dev/null" # record Sent bytes to a file

class Toggle():
    def __init__(self, win, y, x, key, choices, hint=None, current=0):
        self.win = win
        self.y, self.x = y, x
        self.key = key
        self.hint = hint
        self.choices = choices
        self.current = current
        self.smaxlen = max(map(len, self.choices))
        self.display()
        
    def nextState(self):
        self.current = (self.current + 1) % len(self.choices)
        self.display()
        
    def maxLen(self):
        return max(map(len, s))
        
    def display(self):
        cy, cx = self.win.getyx()
        self.win.addstr(self.y, self.x, " %s " % self.key, widgets.COLOR["key"])
        if self.hint: self.win.addstr("(%s) " % self.hint, widgets.COLOR["hint"])
        self.win.addstr(self.getState().center(self.smaxlen)+" ", widgets.COLOR["state"])
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
        self.display()

    def display(self):
        cy, cx = self.win.getyx()
        self.win.addstr(self.y, self.x, " %s " % self.key, widgets.COLOR["key"])
        self.win.addstr(self.text+" ", widgets.COLOR["state"])
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
        self.out_asc = widgets.TxtWin("", ay-3, ax//2, 0, 0)
        self.out_hex = widgets.TxtWin("Hexdump", ay-3, ax//2, 0, ax//2)
        self.in_str = widgets.Input(3, ax, ay-3, 0)
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

def main(scr):
    #### INIT CURSES, STYLES, GUI ####
    scr.clear()
    scr.nodelay(True)
    scr.getch()

    # Styles (see below)
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)  # header
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Received data
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Sent data
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # ERROR
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK) # offset
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)   # status

    widgets.COLOR = {
        "header" : curses.color_pair(1) + curses.A_BOLD,
        "text"   : curses.color_pair(2),
        "send"   : curses.color_pair(3),
        "error"  : curses.color_pair(4) + curses.A_BOLD,
        "offset" : curses.color_pair(5),
        "key"    : curses.color_pair(6) + curses.A_BOLD,
        "hint"   : curses.color_pair(6) + curses.A_ITALIC,
        "state"  : curses.color_pair(6)
    }
    gui = Gui()

    #### INIT SERIAL PORT ####
    try:
        ser = serial.Serial(DEVICE, BAUD, timeout=.05)
        gui.message("Connected to %s (%d baud)\n\n" % (DEVICE, BAUD))
    except serial.SerialException as e:
        ser = None
        gui.error("CONNECTION FAILED\n\n")
        gui.message(str(e))

    #### MAIN LOOP ####
    while gui.running: 
        gui.in_str.win.refresh()
        c = scr.getch()
        ins = gui.tInp.getState()

        if c == -1 and ser: # no input: poll/read serial
            rx = ser.read()
            while ser.inWaiting() > 0: rx += ser.read(ser.inWaiting())
            if len(rx) > 0:
                gui.show(rx, "text")

        elif 31 < c < 127: # ASCII
            gui.in_str.append(chr(c), ins=="Hex")

        elif 0b11000000 <= c <= 0b11110000 and ins != "Hex": # UTF-8 multibyte
            cp = bytearray([c])
            c = scr.getch()
            while 0b10000000 <= c <= 0b11000000:
                cp.append(c)
                c = scr.getch()
            try:
                gui.in_str.append(cp.decode("utf-8"))
            except:
                gui.message("Invalid Input: "+str(cp)+"\n")

        elif c == 10: # ENTER
            inp = gui.in_str.inp
            end = gui.n2brk[gui.tBrk.getState()]
            if ins == "Text":
                s = (inp + end)
                gui.show(s, "send")
                # trancode to current CP
                if ser: ser.write(s.encode(gui.tAsc.getState(), "ignore"))
                gui.in_str.clear()
            elif ins == "File":
                try:
                    f = open(inp, "rb")
                    gui.message("Reading file... ")
                    s = f.read()
                    gui.show("<Sending file %s : %d bytes>" % (inp, len(s)), "send")
                    if ser: ser.write(s)
                    gui.message("\nTransmission done.\n")
                    f.close()
                    gui.in_str.clear()
                except FileNotFoundError as e:
                    gui.error("File "+inp+" not found\n")
            elif ins == "Hex":
                try:
                    bafh = bytearray.fromhex(inp.upper())
                    gui.show(bafh, "send")
                    if ser: ser.write(bafh)
                    gui.in_str.clear()
                except ValueError:
                    gui.error("Invalid Hex-string\n")

        elif c == curses.KEY_BACKSPACE: gui.in_str.backspace(ins=="Hex")
        elif c == curses.KEY_UP: gui.in_str.goHistory(1)
        elif c == curses.KEY_DOWN: gui.in_str.goHistory(-1)
        
        elif c == curses.KEY_NPAGE: gui.bscroll("down")
        elif c == curses.KEY_PPAGE: gui.bscroll("up")
        elif c == curses.KEY_HOME: gui.bscroll("home")
        elif c == curses.KEY_END: gui.bscroll("end")

        elif c in gui.keys: gui.keys[c].action()
        elif c in gui.toggles: gui.toggles[c].nextState()
        
        #else: gui.message("Unmapped key %d\n" % c)
        

curses.wrapper(main)

