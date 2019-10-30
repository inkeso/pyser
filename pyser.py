#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Full featured serial console but with a fancy ncurses-TUI.

import re
import curses
#import serial
from collections import deque

# https://docs.python.org/3/howto/curses.html
# https://docs.python.org/3/library/curses.html

# CONFIG (TODO: getopts)
DEVICE="/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"
BUFFERSIZE = 10000 # number of lines to keep in scrollback
RECDUMP = "/dev/null" # record Received bytes to a file
SNDDUMP = "/dev/null" # record Sent bytes to a file


class receiveBuffer():
    """
    Wrapper for a string not exceeding a specific length.
    Also functions for "rendering" said string.
    """
    def __init__():
        self.hexbuffer = []
        self.ascbuffer = []
    
    def append(self, s):
        # TODO: The performance may suck at the moment,test and optimize later.
        s = "\n asdf \n ghjk \r\n\n\n\r\r\r" ## ??
        
        sa = s.replace("\r", "\n")
        sa = re.split("\n+", sa)
        # OK, jetzt noch umbrechen wenn 
        
        
    
    def rAscii(self, h, w, offset):
        """render a section as ascii.
        return a list with up to `h` strings, each no longer then `w` characters
        offset is used for scrolling.
        """
        s = self.buffer[-(w*h):]
        
    

class sWin(): 
    """Simple widget for displaying text and allowing for scroll"""
    def __init__(self, title, h, w, y, x):
        self.coords = (h,w,y,x) 
        self.title = title
        self.win = curses.newwin(h,w,y,x)
        self.scrollpos = 0
        self.buffer = ""
        self.display()

    def display(self):
        self.win.erase()
        self.win.border()
        self.win.addstr(0, 3, " %s " % self.title, curses.color_pair(1) + curses.A_BOLD)
        
        self.win.addstr(1, 1, self.buffer)
        self.win.refresh()

    def append(self, s):
        self.buffer += s
        # limit max. buffer size to
        self.display()


lips = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris."


def main(scr):
    scr.clear()
    # We can determine the size of the screen by using the curses.LINES and curses.COLS variables

    # Styles
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE) # header


    # let's create two windows for display stuff from DEVICE (ASCII and HEX)
    out_asc = sWin("Received (Text)", 25, 80, 0, 0)
    out_hex = sWin("Received (Hex)", 25, 80, 0, 80)
    
    out_asc.append("Lorem ipsum dolor sit amet consectetur adipisci ach was weiß denn ich wie der Kladderadatsch hier weitergeht haptsache ich habe einen scheißlangen teststring mit keinem einzigen Umbruch... Na, was machste JETZT curses? Fluchen? (gnihi)\n\n")

    # and now wait for some input in a box
    in_str = curses.newwin(3,80,25,0)
    in_str.border()
    in_str.move(1,1)
    in_str.refresh()
    curses.echo()
    
    
    foo =""
    while foo != "quit":
        foo = in_str.getstr().decode()
        out_asc.append(foo+"\n")
        out_hex.append(" ".join([hex(ord(x)) for x in foo]))
        
        in_str.erase()
        in_str.border()
        in_str.move(1,1)
        in_str.refresh()
        
        
curses.wrapper(main)

