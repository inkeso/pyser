# PySer

This is a serial monitor/console intended as a replacement for Arduino-IDE serial monitor.

I wanted something with a featureset like cutecom, but in a terminal. And here we go. A python/curses TUI for serial communication.

→ [Screenshots](https://github.com/inkeso/showcase/tree/master/pyser)

Terminal size must be at least 80x25, for best results use 160 columns or more.
It supports 256 colors, if terminal is capable. Colors can be customized in `styles.py`.

## Commandline parameters
```
$ ./pyser.py --help
usage: pyser.py [-h] [-r BAUDRATE] [-p PARAM] [-t TIMEOUT] [-x] [-c] [-d] [-n] [-da DUMPALL] [-dr DUMPREC] [-ds DUMPSND] [-s PADSIZE] [-m MAXFILEHEX] [port]

positional arguments:
  port                  Device name or None

optional arguments:
  -h, --help            show this help message and exit
  -r BAUDRATE, --baudrate BAUDRATE
                        May be 50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800,
                        9600 (default), 19200, 38400, 57600, 115200, 230400, 460800, 500000,
                        576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000,
                        3500000, 4000000
                        
  -p PARAM, --param PARAM
                        B,P,S <B>-bytesize: Number of data bits. Possible values: 5-8 <P>-parity: Enable parity checking. Possible values: N (None), E (Even), O (Odd) M (Mark), S (Space)
                        <S>-stopbits: Number of stop bits. Possible values: 1, 1.5, 2
                        Default is 8,N,1
  -t TIMEOUT, --timeout TIMEOUT
                        Set a read timeout value. Default is 0.05.
  -x, --xonxoff         Enable software flow control
  -c, --rtscts          Enable hardware (RTS/CTS) flow control
  -d, --dsrdtr          Enable hardware (DSR/DTR) flow control
  -n, --nonexclusive    Don't Set exclusive access mode (POSIX only). A port cannot be opened in exclusive access mode if it is already open in exclusive access mode.
  -da DUMPALL, --dumpall DUMPALL
                        record both received and sent bytes in one file
  -dr DUMPREC, --dumprec DUMPREC
                        record received bytes to a file
  -ds DUMPSND, --dumpsnd DUMPSND
                        record sent bytes to a file
  -s PADSIZE, --padsize PADSIZE
                        number of lines to keep in scrollback-pad (max. 32767, default 2000)
  -m MAXFILEHEX, --maxfilehex MAXFILEHEX
                        when uploading a file, only files smaller then this are displayed in the hexdump. For larger files, a placeholder is shown. (max. 16 * padsize, default 4 KiB)
```

## Keys
```
F1: Show this help
F2: pause / continue autoscrolling
F4: Clear views / reset counter
F5: Select Input mode (See below)
F6: Append Line-ending on send (Text)
F7: Switch codepage for Textview
F8: Toggle display in/out in hexdump

F10: Quit

PgUp/PgDn: Scroll ⅓ Page up/down
Home/End : Scroll to top or bottom

↓/↑ : go through input-history
```

## Input Modes

### Text
Input text with keyboard. Hit Enter to send. Characters above 7 bit ASCII will
be translated to selected codepage. If a special character can not be 
translated, it is omited (check hexdump). If a Line-end (F6) is selected, it 
will be appended to the sent string.

### Hex
send binary data: input hex-bytes to be sent (on enter). Only accepts 0-9 a-f.
Each byte must be 2 chars.

### File
Send a file (binary). In this mode, you can input a valid file- or dir- name.
In case of a directory, it's content is displayed and nothing is sent to the
serial port. E.g.: use "." to view the content of the current dir.
If inout is a valid, readable file, its content is sent unaltered.
The content of the file is displayed in the hexdump as well, if the file is 
small enough (default: 4kb). Otherwise a placeholder is shown. The input is 
taken literally, so you don't have to escape spaces in file- names or something.
You can use TAB to complete filenames (or display ambiguous matches).

Be aware that the whole file is read to memory before sending, so don't try to
transfer very huge files.

### TODO
 - Real line editing
 - Better resize handling: Redraw content of both panels instead of clearing
 - Set default line ending (F6) on commandline or outodetect from serial input?
 - Probably rearrange some buttons / keys
