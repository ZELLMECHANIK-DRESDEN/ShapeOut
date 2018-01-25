#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test batch control
"""
from __future__ import print_function

from shapeout.gui.confparms import get_config_entry_choices, get_config_entry_dtype


def test_config_choices():
    c1 = get_config_entry_choices("plotting", "kde")
    for c2 in ["none", "gauss", "multivariate"]:
        assert c2 in c1

    c3 = get_config_entry_choices("Plotting", "Axis X")
    assert len(c3) != 0
    assert "deform" in c3

    c3 = get_config_entry_choices("Plotting", "Axis Y", ignore_axes=["deform"])
    assert len(c3) != 0
    assert "deform" not in c3

    c4 = get_config_entry_choices("Plotting", "Rows")
    assert "1" in c4

    c5 = get_config_entry_choices("Plotting", "Scatter Marker Size")
    assert "1" in c5

    c6 = get_config_entry_choices("Plotting", "Scale Axis")
    assert "linear" in c6


def test_config_dtype():
    a = get_config_entry_dtype("filtering", "enable filters")
    assert a == bool

    a = get_config_entry_dtype("setup", "channel width")
    assert a == float

    a = get_config_entry_dtype("setup", "unknown variable")
    assert a == float


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
