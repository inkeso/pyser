#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Full featured serial console but with a fancy ncurses-TUI.

import curses
import serial


# https://docs.python.org/3/howto/curses.html
# https://docs.python.org/3/library/curses.html

DEVICE="/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"

# Styles
curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE) # header


class sWin(): # boah, widget :)
    def __init__(self, title, h, w, y, x)
        self.win = curses.newwin(h,w,y,x)
        self.win.border()
        self.curpos = [0,1]
        self.win.addstr(0, 3, title, curses.color_pair(1) + curses.A_BOLD)
        self.refresh()

    def append(self, s):
        # denk dran \r zu entfernen... oder besser "\r?\n" → "\n"; "\r" → "\n"
        self.win.addstr(self.curpos[0], out_asc_curpos[1], foo)
        self.refresh()
        # TODOOO

def main(scr):
    scr.clear() # scr is also a window. remember to .redraw()
    # We can determine the size of the screen by using the curses.LINES and curses.COLS variables

    # let's create two windows for display stuff from DEVICE (ASCII and HEX)
    out_asc = curses.newwin(25, 80, 0, 0)
    out_asc.border()
    out_asc_curpos = [0,1]
    out_asc.addstr(0,3,"ASCII", curses.color_pair(1) + curses.A_BOLD) # denk dran \r zu entfernen... oder besser "\r?\n" → "\n"; "\r" → "\n"
    out_asc.refresh()
    
    # with attributes...
    out_hex = curses.newwin(25, 80, 0, 80)
    out_hex.border()
    out_hex.addstr(0,3,"HEX", curses.color_pair(1) + curses.A_BOLD)
    out_hex.refresh()
    
    # and now wait for some input in a box
    in_str = curses.newwin(3,80,25,0)
    in_str.border()
    in_str.move(1,1)
    in_str.refresh()
    curses.echo()
    foo =""
    while foo != b"quit":
        foo = in_str.getstr()
        out_asc_curpos[0] += 1
        out_asc.addstr(out_asc_curpos[0], out_asc_curpos[1], foo)
        out_asc.refresh()
        
        in_str.erase()
        in_str.border()
        in_str.move(1,1)
        in_str.refresh()
        
        
    


curses.wrapper(main)

