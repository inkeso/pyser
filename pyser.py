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


import curses
import serial
import widgets
# https://docs.python.org/3/howto/curses.html
# https://docs.python.org/3/library/curses.html

# CONFIG (TODO: getopts)
DEVICE = "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"
BAUD = 9600
widgets.TxtWin.PADSIZE = 200 # number of lines to keep in scrollback-pad
RECDUMP = "/dev/null" # record Received bytes to a file
SNDDUMP = "/dev/null" # record Sent bytes to a file

lips = "Lörem ipsüm → dolor sit amet, consectetur 😉 adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris nisi utaliquip ex ea commodo consequat. Duis aute irure dolor inreprehenderit in voluptate velit esse cillum dolore eu fugiat nullapariatur. Excepteur sint occaecat cupidatat non proident, sunt inculpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enimad minim veniam, quis nostrud exercitation ullamco laboris."


class Gui():
    HELP = """
        F1 : Show this help
        F2 : Pause/Unpause transmission                  [TODO]
        F4 : Clear Views / reset counter
        F5 : Toggle Input mode (ASCII/Hex/File)          [TODO]
        F6 : Toggle CR/LF after input on send
        F7 : Toggle Translation (in textview)
        F8 : Toggle display of input / output in hexdump
        F10: Quit
        
        PgUp/PgDn: Scroll ⅓ Page up/down
        Home/End : Scroll to top or bottom
        
        ↓/↑ : go through input-history (repeat command)
    \n"""
    
    def __init__(self):
        ay, ax = curses.LINES, curses.COLS
        self.out_asc = widgets.TxtWin("", ay-3, ax//2, 0, 0)
        self.out_asc.showTranslate()
        self.out_hex = widgets.TxtWin("Hexdump", ay-3, ax//2, 0, ax//2)
        self.out_hex.showHex()
        self.in_str = widgets.Input(3, ax, ay-3, 0)

    def show(self, s, color): # show stuff in both views and scroll to bottom
        self.out_asc.append(s, color)
        if (self.out_hex.inHex == 0) \
            or (self.out_hex.inHex == 1 and color=="text") \
            or (self.out_hex.inHex == 2 and color=="send"):
            self.out_hex.appendHex(s, color)
        # toggle off? pause?
        self.out_hex.scroll("end")
        self.out_asc.scroll("end") 
        
        
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
        self.out_asc.scroll("end")
        self.out_hex.scroll("end")

def main(scr):
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

    # Prepare Serial Port
    try:
        ser = serial.Serial(DEVICE, BAUD)
        gui.message("Connected to %s (%d baud)\n\n" % (DEVICE, BAUD))
        ser.timeout=.05
    except serial.SerialException as e:
        ser = None
        gui.error("CONNECTION FAILED\n\n")
        gui.message(str(e))
    
    while True:
        gui.in_str.win.refresh()
        c = scr.getch()

        # TODO: Inputhandling kann so nich bleiben. aber erstmal langts.
        # Also je nach Modus wäre ja GNU readline geil...
        if c == -1: # no input
            if ser:
                rx = ser.read()
                while ser.inWaiting() > 0: rx += ser.read(ser.inWaiting())
                if len(rx) > 0: 
                    data = "".join(chr(x) for x in rx)
                    gui.show(data, "text")
        
        elif 31 < c < 127: # ASCII
            gui.in_str.append(chr(c))
        
        elif c == 10: # ENTER
            gui.show(gui.in_str.getInput(), "send")
            if ser: ser.write(gui.in_str.getBytes())
            gui.in_str.clear()
    
        elif c == curses.KEY_BACKSPACE: gui.in_str.backspace()
        elif c == curses.KEY_UP: gui.in_str.goHistory(1)
        elif c == curses.KEY_DOWN: gui.in_str.goHistory(-1)

        elif c == curses.KEY_F1: gui.message(gui.HELP)
        elif c == curses.KEY_F2: pass
        elif c == curses.KEY_F4: gui.emptyView()
        elif c == curses.KEY_F5: gui.in_str.nextState()
        elif c == curses.KEY_F6: gui.in_str.nextBreak()
        elif c == curses.KEY_F7: gui.out_asc.nextTranslate()
        elif c == curses.KEY_F8: gui.out_hex.nextHex()
        elif c == curses.KEY_F10: return

        elif c == curses.KEY_NPAGE: gui.bscroll("down")
        elif c == curses.KEY_PPAGE: gui.bscroll("up")
        elif c == curses.KEY_HOME: gui.bscroll("home")
        elif c == curses.KEY_END: gui.bscroll("end")

        elif c == curses.KEY_F11: gui.show(lips, "send") # For fun an testing

        #else:
        #    out_asc.append("Ignored Key: %d\n" % c , "offset")
        #    out_asc.display()
        
curses.wrapper(main)

