#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import tempfile

import dclab
import numpy as np

from shapeout import analysis

from helper_methods import example_data_dict


def test_basic():
    ddict = example_data_dict(size=8472)
    ds = dclab.new_dataset(ddict)
    anal = analysis.Analysis([ds])
    
    assert len(anal.measurements) == 1


def test_data_size():
    dicts = [ example_data_dict(s) for s in [10, 100, 12, 382] ]
    anal = analysis.Analysis([dclab.new_dataset(d) for d in dicts])
    
    minsize = anal.ForceSameDataSize()
    assert minsize == 10
    for mm in anal.measurements:
        assert np.sum(mm._filter) == minsize


def test_axes_usable():
    keys = ["area_um", "circ"]
    dicts = [ example_data_dict(s, keys=keys) for s in [10, 100, 12, 382] ]
    anal = analysis.Analysis([dclab.new_dataset(d) for d in dicts])
    
    axes = anal.GetUsableAxes()
    for ax in keys:
        assert ax in axes



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
