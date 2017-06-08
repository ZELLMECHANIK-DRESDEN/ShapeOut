#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function
import sys
from os.path import abspath, dirname

import numpy as np
import tempfile

import dclab

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
from shapeout import analysis

from helper_methods import example_data_dict


def test_basic():
    ddict = example_data_dict(size=8472)
    ds = dclab.RTDC_DataSet(ddict=ddict)
    anal = analysis.Analysis([ds])
    
    assert len(anal.measurements) == 1


def test_dump():
    dicts = [ example_data_dict(s) for s in [10, 100, 12, 382] ]
    anal = analysis.Analysis([dclab.RTDC_DataSet(ddict=d) for d in dicts])
    
    odir = tempfile.mkdtemp()
    try:
        anal.DumpData(odir)
    except AssertionError:
        pass
    else:
        raise ValueError("Dumping non-tdms data should not work")
    

def test_data_size():
    dicts = [ example_data_dict(s) for s in [10, 100, 12, 382] ]
    anal = analysis.Analysis([dclab.RTDC_DataSet(ddict=d) for d in dicts])
    
    minsize = anal.ForceSameDataSize()
    assert minsize == 10
    for mm in anal.measurements:
        assert np.sum(mm._filter) == minsize


def test_axes_usable():
    keys = ["area", "circ"]
    dicts = [ example_data_dict(s, keys=keys) for s in [10, 100, 12, 382] ]
    anal = analysis.Analysis([dclab.RTDC_DataSet(ddict=d) for d in dicts])
    
    axes = anal.GetUsableAxes()
    for ax in keys:
        assert ax in axes



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
