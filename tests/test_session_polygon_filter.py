#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import os.path as op

import dclab

from shapeout.session import conversion

from helper_methods import extract_session, cleanup


def test_polygon():
    """
    In versions before 0.7.6, polygons in dclab were exported with
    other column names.
    """
    sdir, _path = extract_session("session_v0.6.0.zmso")
    pfile = op.join(sdir, "PolygonFilters.poly")
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
        outfile.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
