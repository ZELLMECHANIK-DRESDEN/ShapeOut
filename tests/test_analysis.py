#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import dclab
import numpy as np

from shapeout import analysis

from helper_methods import example_data_dict


def test_basic():
    ddict = example_data_dict(size=8472)
    ds = dclab.new_dataset(ddict)
    anal = analysis.Analysis([ds])

    assert len(anal.measurements) == 1


def test_get_feat_range_opt():
    keys = ["area_um", "deform", "fl1_max"]
    dicts = [example_data_dict(s, keys) for s in [10, 100, 12, 382]]
    # add a fl2_max column with negative numbers
    for dd in dicts:
        lend = len(dd["deform"])
        dd["fl2_max"] = np.linspace(-1, 5000, lend)
        dd["userdef1"] = np.linspace(-2, -3, lend)
        dd["userdef2"] = np.linspace(-1, 1, lend)
    #dicts.append(otherdict)
    anal = analysis.Analysis([dclab.new_dataset(d) for d in dicts])
    assert anal.get_feat_range_opt(feature="deform") == (0, .2)
    assert np.allclose(anal.get_feat_range_opt(feature="area_um"),
                       (0.000507009623987198, 0.9989715591819257))
    assert np.allclose(anal.get_feat_range_opt(feature="fl1_max"),
                       (0.0036766675498647317, 0.9970937546290722))
    assert np.allclose(anal.get_feat_range_opt(feature="fl1_max", scale="log"),
                       (0.0036766675498647317, 0.9970937546290722))
    assert np.allclose(anal.get_feat_range_opt(feature="fl2_max"),
                       (-1, 5000))
    assert np.allclose(anal.get_feat_range_opt(feature="fl2_max", scale="log"),
                       (1, 5000))
    assert np.allclose(anal.get_feat_range_opt(feature="userdef1"),
                       (-3, -2))
    assert np.allclose(anal.get_feat_range_opt(feature="userdef1", scale="log"),
                       (.1, 1))
    assert np.allclose(anal.get_feat_range_opt(feature="userdef2"),
                       (-1, 1))
    assert np.allclose(anal.get_feat_range_opt(feature="userdef2", scale="log"),
                       (0.051197602631569354, 1.0))


def test_get_config_value():
    ddict = example_data_dict(size=8472)
    ds1 = dclab.new_dataset(ddict)
    ds2 = dclab.new_dataset(ddict)
    ds1.config["filtering"]["deform max"] = .5
    ds2.config["filtering"]["deform max"] = .2
    ds1.config["filtering"]["deform min"] = .0
    ds2.config["filtering"]["deform min"] = .0
    anal = analysis.Analysis([ds1, ds2])
    assert anal.get_config_value(section="filtering", key="deform min") == 0
    try:
        anal.get_config_value(section="filtering", key="deform max")
    except analysis.MultipleValuesError:
        pass
    else:
        assert False, "different values should raise error"
    

def test_data_size():
    dicts = [example_data_dict(s) for s in [10, 100, 12, 382]]
    anal = analysis.Analysis([dclab.new_dataset(d) for d in dicts])

    minsize = anal.ForceSameDataSize()
    assert minsize == 10
    for mm in anal.measurements:
        assert np.sum(mm._filter) == minsize


def test_axes_usable():
    keys = ["area_um", "circ"]
    dicts = [example_data_dict(s, keys=keys) for s in [10, 100, 12, 382]]
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
