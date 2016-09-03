#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Scripted tests for the user interface.
"""
from __future__ import division, print_function
import sys
from os.path import abspath, dirname

import numpy as np
import tempfile

import dclab

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import shapeout


def test_prepare():
    from shapeout.__main__ import prepare_app
    prepare_app()


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
