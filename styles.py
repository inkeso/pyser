#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Styles

def psblack(curses):
    if curses.COLORS >= 256:
        curses.init_pair(1, 244, curses.COLOR_BLACK)                 # header/border
        curses.init_pair(2, 254, curses.COLOR_BLACK)                 # Received data
        curses.init_pair(3, 85,  curses.COLOR_BLACK)                 # Sent data
        curses.init_pair(4, 196, curses.COLOR_BLACK)                 # ERROR
        curses.init_pair(5, 222, curses.COLOR_BLACK)                 # offset / messages
        curses.init_pair(6, 15,  18)                                 # status key
        curses.init_pair(7, 248, 18)                                 # status info
        curses.init_pair(8, 11,  18)                                 # status itself
    else:
        curses.init_pair(1, curses.COLOR_BLACK,  curses.COLOR_BLACK) # header/border
        curses.init_pair(2, curses.COLOR_WHITE,  curses.COLOR_BLACK) # Received data
        curses.init_pair(3, curses.COLOR_CYAN,   curses.COLOR_BLACK) # Sent data
        curses.init_pair(4, curses.COLOR_RED,    curses.COLOR_BLACK) # ERROR
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK) # offset / messages
        curses.init_pair(6, curses.COLOR_WHITE,  curses.COLOR_BLUE)  # status key
        curses.init_pair(7, curses.COLOR_WHITE,  curses.COLOR_BLUE)  # status info
        curses.init_pair(8, curses.COLOR_YELLOW, curses.COLOR_BLUE)  # status itself
    return {
        "header" : curses.color_pair(1) + (curses.A_BOLD if curses.COLORS < 256 else 0),
        "text"   : curses.color_pair(2),
        "send"   : curses.color_pair(3),
        "error"  : curses.color_pair(4) + (curses.A_BOLD if curses.COLORS < 256 else 0),
        "offset" : curses.color_pair(5),
        "key"    : curses.color_pair(6) + curses.A_BOLD,
        "hint"   : curses.color_pair(7),
        "state"  : curses.color_pair(8) + (curses.A_BOLD if curses.COLORS < 256 else 0),
    }





CURRENT = psblack
