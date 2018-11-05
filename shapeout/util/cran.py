#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The R binary `rcmd` is set on the first import of this module.
If you wish to change the path of the R command, you can do so
by modifying this variable here.
"""

from __future__ import print_function
import os
import subprocess as sp
import sys


def get_R_binary(verbose=False):
    """
    Searches for an R binary in locations according to the following
    order:
       
   
    - Windows
      The R binary is usually located somewhere in 
      
          C:\\Program Files\\R\\*\\bin\\i386
    

    - Frozen system
      If this is a package like Shape-Out, then the binary installer supplied us
      with an R binary located in
       
          sys._MEIPASS
    
    - Linux
    
          /usr/bin
    
    
    In all of these folders, the files "R" or "R.exe" is searched and the
    first existing file is returned.
    """
    # additional search paths
    Rpaths = []

    append_folders = ["", "bin\\i386"]
    # Make sure that the R installation that comes with
    # Shape-Out is the first choice in a frozen win application.
    if hasattr(sys, "frozen"):
        Rroot_win_frozen = os.path.join(os.path.abspath(sys._MEIPASS), "R")  # @UndefinedVariable
        if os.path.exists(Rroot_win_frozen):
            for append in append_folders:
                Rpaths += [  os.path.join(Rroot_win_frozen, os.path.join(d,append)) for d in os.listdir(Rroot_win_frozen) ]

    # Win regular
    Rroot_win = "C:\\Program Files\\R"
    if os.path.exists(Rroot_win):
        for append in append_folders:
            # This will work independent of the installed R version
            Rpaths += [ os.path.join(Rroot_win, os.path.join(d,append)) for d in os.listdir(Rroot_win) ]

    # linux
    Rpaths += ["/usr/bin"]

    Rexes = []
    for binary in ["R", "R.exe"]:
        Rexes += [ os.path.join(loc, binary) for loc in Rpaths ]

    Rexe_avail = [ r for r in Rexes if os.path.exists(r) ]

    if verbose:
        print("Available binaries:", Rexe_avail)

    # standard path search:
    if len(Rexe_avail) == 0:
        Rexe = "R"
    else:
        Rexe = Rexe_avail[0]

    # find other installation:
    if verbose: 
        print("Using R: ", Rexe)
    
    return Rexe


def get_R_version(binary=None):
    """
    Returns version string and platform output of `R --version`.
    
    Parameters
    ----------
    binary : str or None
        Path to R binary. If not given, then the variable `cran.rcmd` is
        used instead.
        
    Returns
    -------
    version : str
        R version string that looks like this:
            R version 3.0.2 (2013-09-25) -- "Frisbee Sailing"
            Copyright (C) 2013 The R Foundation for Statistical Computing
            Platform: x86_64-pc-linux-gnu (64-bit)
    """
    global rcmd
    
    if binary is not None:
        rcmd = binary

    # Get version string
    try:
        p = sp.Popen('"{}" --version'.format(rcmd), stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        ver = "\n".join(p.communicate()).strip() 
        ver = ver.split("\n")
        ver = [ v.strip() for v in ver ]
        ver = "\n".join([rcmd]+ver[:3])
    except:
        ver = "\n".join([rcmd, "Could not determine R version."])
    
    return ver


rcmd = get_R_binary(verbose=True)