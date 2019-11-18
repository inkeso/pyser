#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Full featured serial console like cuteterm, but with a fancy ncurses-TUI.

# TODO:
# - Parameter via getopt
# - write input/output to file (seperate and/or combined)
# - documentation/readme
# - Better resize (don't clear/repopulate... this will be interesting)

# https://docs.python.org/3/howto/curses.html
# https://docs.python.org/3/library/curses.html
# https://pyserial.readthedocs.io/

import sys
import curses
#import serial
import serdummy as serial
import finput
import widgets
import translate

DEVICE = "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0XXX"
BAUD = 9600
# port – Device name or None.
# baudrate=9600 (int) – Baud rate such as 9600 or 115200 etc.
# bytesize=8 – Number of data bits. Possible values: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
# parity='N' – Enable parity checking. Possible values: PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE
# stopbits=1 – Number of stop bits. Possible values: STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
# timeout=0.05 (float) – Set a read timeout value.
# xonxoff=False (bool) – Enable software flow control.
# rtscts=False (bool) – Enable hardware (RTS/CTS) flow control.
# dsrdtr=False (bool) – Enable hardware (DSR/DTR) flow control.
# exclusive=True (bool) – Set exclusive access mode (POSIX only). A port cannot be opened in exclusive access mode if it is already open in exclusive access mode.
widgets.TxtWin.PADSIZE = 2000 # number of lines to keep in scrollback-pad # MAX: 32767
RECDUMP = None # record received bytes to a file
SNDDUMP = None # record sent bytes to a file
BTHDUMP = None # record both in one file

MAXFILEHEXDUMP = 4096 # when uploading a file, only files smaller then this are displayed in the hexdump. for larger files, a placeholder is shown. # MAX: 16*PADSIZE

def launch():
    #GETOPT ...
    
    
    # Start!
    try:
        curses.wrapper(tuimain, Iserial())
    except Exception as e:
        print("ERROR: "+str(e))
        try: eno = e.errno
        except: eno = 100
        return eno

class Iserial():
    """wrap serial read and write functions for logging"""
    def __init__(self):
        self.ser = serial.Serial(DEVICE, BAUD, timeout=.05, exclusive=True)
    
    def read(self):
        rx = self.ser.read()
        while self.ser.inWaiting() > 0: rx += self.ser.read(self.ser.inWaiting())
        # TODO: write to file
        return rx
    
    def write(self,s):
        self.ser.write(s)
        # TODO: write to file

def tuimain(scr, ser):
    #### INIT CURSES, STYLES, GUI ####
    scr.clear()
    scr.nodelay(True)
    scr.getch()

    # Styles (see below)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLACK)  # header/border
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
    gui = widgets.Gui()
    gui.message("Connected to %s (%d baud)\n\n" % (DEVICE, BAUD))

    #### MAIN LOOP ####
    while gui.running: 
        gui.in_str.win.refresh()
        c = scr.getch()
        ins = gui.tInp.getState()

        if c == -1 and ser: # no input: poll/read serial
            rx = ser.read()
            if len(rx) > 0: gui.show(rx, "text")

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
                f = finput.tryget(inp)
                gui.message(f[1]+"\n") if f[2] else gui.error(f[1]+"\n")
                if f[0]:
                    s = f[0].read()
                    if ser: ser.write(s)
                    if len(s) <= MAXFILEHEXDUMP:
                        gui.hexdump(s, "send")
                    else: # don't relay dump it
                        gui.hexdump("[BINARY DATA %d BYTES]".encode("ASCII") % len(s), "send")
                    gui.message("Transmission done.\n")
                    f[0].close()
                gui.in_str.clear()
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
        
        elif c == curses.KEY_RESIZE:
            # TODO: gracefully resize. 
            # Starting over / clearing everything is ugly.
            curses.LINES, curses.COLS = scr.getmaxyx()
            gui = widgets.Gui()
        
        #else: gui.message("Unmapped key %d\n" % c)

if __name__ == '__main__': sys.exit(launch())
