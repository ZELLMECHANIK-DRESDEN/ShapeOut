#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

from pkg_resources import resource_filename  # @UnresolvedImport
import os
import numpy as np
import sys

from .spath import path_to_str, safe_path


def float2string_nsf(fval, n=7):
    """
    Truncate a float to n significant figures and return nice string.
    Arguments:
      q : a float
      n : desired number of significant figures
    Returns:
    String with only n s.f. and trailing zeros.
    """
    #sgn=np.sign(fval)
    if fval == 0:
        npoint=n
    elif np.isnan(fval):
        return "NaN"
    else:
        q=abs(fval)
        k=int(np.ceil(np.log10(q/n)))
        # prevent negative significant digits
        npoint = max(0, n-k)
    string="{:.{}f}".format(fval, npoint)
    return string


def nice_string(string):
    """
    Convert a string of a float created by `float2string_nsf`
    to something nicer.
    
    i.e.
    - 1.000000 -> 1
    - 1.010000 -> 1.010
    """
    if len(string.split(".")[1].replace("0", "")) == 0:
        return "{:d}".format(int(float(string)))
    else:
        olen = len(string)
        newstring = string.rstrip("0")
        if olen > len(newstring):
            string=newstring+"0"
        return string


def nice_float2string(fval, n=3):
    """
    wraps around float2string_nsf and nice_string
    """
    strfloat = float2string_nsf(fval, n=n)
    return nice_string(strfloat)
    

def hex_to_rgb(value):
    """
    hex_to_rgb("#ffffff")             #==> (255, 255, 255)
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(rgb, norm=255):
    """
    rgb_to_hex((255, 255, 255))       #==> '#ffffff'
    rgb_to_hex((1, 1, 1), norm=1)       #==> '#ffffff'
    """
    rgb = [ i*255/norm for i in list(rgb) ]
    return '#%02x%02x%02x' % tuple(rgb)
