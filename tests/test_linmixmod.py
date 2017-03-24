#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
For this test to work, this must be installed
 
 - Python package pyper
 - R-base
 - R package 'lme4'

"""
from __future__ import division, print_function, unicode_literals
import sys
from os.path import abspath, dirname

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
from shapeout.lin_mix_mod import linmixmod


def test_linmixmod():
    treatment = ['Control', 'Drug', 'Control', 'Drug']
    timeunit = [1, 1, 2, 2]
    xs = [
          [100,99,80,120,140,150,100,100,110,111,140,145],
          [115,110,90,110,145,155,110,120,115,120,120,150,100,90,100],
          [150,150,130,170,190,250,150,150,160,161,180,195,130,120,125,130,125],
          [155,155,135,175,195,255,155,155,165,165,185, 200,135,125,130,135,140,150,135,140]
         ]

    res = linmixmod(xs=xs, treatment=treatment, timeunit=timeunit)
    
    assert np.allclose([res["Estimate"]], [136.63650509])


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
