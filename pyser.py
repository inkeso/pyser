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
    
    
    # We can determine the size of the screen by using the curses.LINES and curses.COLS variables
    # let's create two windows for display stuff from DEVICE (ASCII and HEX)
    ay, ax = curses.LINES, curses.COLS
    
    out_asc = widgets.TxtWin("", ay-3, ax//2, 0, 0)
    out_asc.showTranslate()
    out_hex = widgets.TxtWin("Hexdump", ay-3, ax//2, 0, ax//2)
    in_str = widgets.Input(3, ax, ay-3, 0)

    # Prepare Serial Port
    try:
        ser = serial.Serial(DEVICE, BAUD)
        out_asc.append("\nConnected to %s (%d baud)\n\n" % (DEVICE, BAUD), "offset")
        ser.timeout=.05
    except serial.SerialException as e:
        ser = None
        out_asc.append("\nCONNECTION FAILED\n\n", "error")
        out_asc.append(str(e))

    out_asc.display()
    
    
    while True:
        in_str.win.refresh()
        c = scr.getch()

        # TODO: Inputhandling kann so nich bleiben. aber erstmal langts.
        # Also je nach Modus wäre ja GNU readline geil...
        if c == -1: # no input
            if ser:
                rx = ser.read()
                while ser.inWaiting() > 0: rx += ser.read(ser.inWaiting())
                if len(rx) > 0: 
                    data = "".join(chr(x) for x in rx)
                    out_asc.append(data, "text")
                    out_hex.appendHex(data, "text")
                    out_asc.scroll("end") # toggle off? pause?
                    out_hex.scroll("end") # toggle off? pause?
            
        elif 31 < c < 127: # ASCII
            in_str.append(chr(c))
        
        elif c == 10: # ENTER
            out_asc.append(in_str.getInput(), "send")
            out_hex.appendHex(in_str.getInput(), "send")
            if ser: ser.write(in_str.getBytes())
            in_str.clear()
    
        elif c == curses.KEY_BACKSPACE: in_str.backspace()
        elif c == curses.KEY_UP: in_str.goHistory(1)
        elif c == curses.KEY_DOWN: in_str.goHistory(-1)
        
        elif c == curses.KEY_F1:
            out_asc.append("""
            F1 : Show this help
            F2 : Pause/Unpause transmission                  [TODO]
            F5 : Toggle Input mode (ASCII/Hex/File)          [TODO]
            F6 : Toggle CR/LF after input on send
            F7 : Toggle Translation (in textview)
            F8 : Toggle display of input / output in hexdump [TODO]
            F10: Quit
            PgUp/PgDn: Scroll ⅓ Page up/down
            Home/End : Scroll to top or bottom
            ↓/↑ : go through input-history (repeat command)
            \n""", "offset")
            out_asc.scroll("end")
            
        elif c == curses.KEY_F2:
            pass
        
        elif c == curses.KEY_F5: in_str.nextState()
        elif c == curses.KEY_F6: in_str.nextBreak()
        elif c == curses.KEY_F7: out_asc.nextTranslate()

        elif c == curses.KEY_F10:
            return
        
        elif c == curses.KEY_F11: # FUN: insert lorem ipsum (test, no write to ser)
            out_asc.append(lips, "send")
            out_hex.appendHex(lips, "send")
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
        else:
            out_asc.append("Unkown Key: %d\n" % c , "offset")
            out_asc.display()
        
        #foo = in_str.getstr().decode()
        #out_asc.append(foo+"\n")
        #out_hex.append(" ".join([hex(ord(x)) for x in foo]))
        
curses.wrapper(main)

