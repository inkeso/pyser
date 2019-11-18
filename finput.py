#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Some helpers for file input.


import os


def humansize(s):
    '''
    Return a string representing a human readable representation of a
    filesize
    '''
    _abbrevs = [(1<<50,'PiB'), (1<<40,'TiB'), (1<<30,'GiB'), 
                (1<<20,'MiB'), (1<<10,'KiB'), (1, 'B')]
    size = os.path.getsize(s)
    for factor, suffix in _abbrevs:
        if size >= factor: break
    if suffix == 'B': return '%d %s' % (size/float(factor), suffix)
    return '%0.2f %s' % (size/float(factor), suffix)


def tryget(s):
    """
    Try and get contents of s. Return a tuple of: (content, message, success)
    - `content` is a file-descriptor, if it's a normal, readable file or None.
    - `message` may contain:
        - the directory-content if s is a dir
        - an informative message about the file being read if s is a file.
        - Some errormessage if anything goes wrong
    - `success` will be False if anything fails (file/dir not found/not readable)
    """
    
    if not os.path.exists(s):
        return (None, s+ " does not exist.", False)
    
    if os.path.isfile(s):
        try:
            f = open(s, "rb")
            t = os.path.getsize(s)
            return(f, "Opened file %s, %d bytes" % (s, t), True)
        except e:
            return (None, str(e), False)
    
    if os.path.isdir(s):
        try:
            d = os.listdir(s)
        except e:
            return (None, str(e), False)
        # expand to tuples (size, name)
        def infotuple(x):
            xp = os.path.join(s,x)
            nfo = "?"
            if os.path.isdir(xp):
                nfo = "<DIR>"
            else:
                try: nfo = humansize(xp)
                except: pass
            return (nfo, x)
        li = [infotuple(x) for x in d]
        # sort dirs first and alphabetically
        dirs = list(filter(lambda x: x[0] == "<DIR>", li))
        dirs.sort(key=lambda x: x[1].upper())
        fils = list(filter(lambda x: x[0] != "<DIR>", li))
        fils.sort(key=lambda x: x[1].upper())
        res = "\n\n----- DIRECTORY %s -----\n\n" % s
        res += "\n".join("%12s %s" % x for x in dirs)
        res += "\n"
        res += "\n".join("%12s %s" % x for x in fils)
        return (None, res, True)
    
    return(None, s+" is not a regular file (or dir)", False)

