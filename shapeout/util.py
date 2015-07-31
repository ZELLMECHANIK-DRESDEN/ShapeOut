#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys


def findfile(fname):
    """ finds the absolute path of a file
    """
    dirs = list()
    # directory names that make sense
    dirs += [".", "lang", "art", "config", "data"]

    dirs += ["../"+dd for dd in dirs]

    thedirs = []
    if hasattr(sys, 'frozen'):
        for d in dirs:
            d = os.path.join("shapeout-data",d)
            thedirs += [os.path.realpath(os.path.join(sys._MEIPASS,d))]  # @UndefinedVariable
    else:
        for d in dirs:
            thedirs += [os.path.realpath(os.path.join(os.path.dirname(__file__),d))]
    # if this does not work:
    for loc in thedirs:
        thechl = os.path.join(loc,fname)
        if os.path.exists(thechl):
            return thechl
    return ""
