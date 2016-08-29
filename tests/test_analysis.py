#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function
import sys
from os.path import abspath, dirname

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
from shapeout import analysis

from helper_methods import retreive_tdms, example_data_sets


def test_basic():
    f = retreive_tdms(example_data_sets[0])
    anal = analysis.Analysis([f])
    
    assert len(anal.measurements) == 1



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
