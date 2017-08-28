#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
from os.path import abspath, dirname, join
import shutil
import sys

import dclab

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from shapeout.session import conversion

from helper_methods import extract_session, cleanup


def test_polygon():
    """
    In versions before 0.7.6, polygons in dclab were exported with
    other column names.
    """
    sdir, _path = extract_session("session_v0.6.0.zmso")
    pfile = join(sdir, "PolygonFilters.poly")
    # conversion
    outfile = conversion.convert_polygon(pfile,
                                         # pretend we don't know the version
                                         version=None,
                                         )
    # load polygon file
    pf = dclab.PolygonFilter(filename=outfile)
    assert pf.axes == (u'area_um', u'deform')
    cleanup()
    try:
        os.remove(outfile)
    except:
        pass
    

if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
