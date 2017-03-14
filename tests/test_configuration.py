#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function
import sys
from os.path import abspath, dirname

import numpy as np
import tempfile
import shutil

import dclab

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
from shapeout import configuration

from helper_methods import example_data_dict


def test_cfg_basic():
    cfg = configuration.ConfigurationFile()
    wd = abspath("./")
    cfg.set_dir(dirname(wd), "Peter")

    assert dirname(wd) == cfg.get_dir("Peter")


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
