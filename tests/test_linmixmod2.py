#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
For this test to work, this must be installed
 
 - Python package pyper
 - R-base
 - R package 'lme4'
"""
from __future__ import division, print_function
import sys
from os.path import abspath, dirname

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
from shapeout.lin_mix_mod import linmixmod

def test_linmixmod():
    xs = [
    [100,99,80,120,140,150,100,100,110,111,140,145], #Larger values (Channel1)
    [20,10,5,16,14,22,27,26,5,10,11,8,15,17,20,9], #Smaller values (Reservoir1)
    [115,110,90,110,145,155,110,120,115,120,120,150,100,90,100], #Larger values (Channel2)
    [30,30,15,26,24,32,37,36,15,20,21,18,25,27,30,19], #Smaller values (Reservoir2)
    [150,150,130,170,190,250,150,150,160,161,180,195,130,120,125,130,125],
    [2,1,5,6,4,2,7,6,5,10,1,8,5,7,2,9,11,8,13],
    [155,155,135,175,195,255,155,155,165,165,185, 200,135,125,130,135,140,150,135,140],
    [25,15,19,26,44,42,35,20,15,10,11,28,35,10,25,13]] 
    treatment1 = ['Control', 'Reservoir Control', 'Control', 'Reservoir Control',\
    'Treatment', 'Reservoir Treatment','Treatment', 'Reservoir Treatment']
    timeunit1 = [1, 1, 2, 2, 1, 1, 2, 2]
    Result_1 = linmixmod(xs=xs,treatment=treatment1,timeunit=timeunit1)
    assert np.allclose([Result_1["Estimate"]], [93.693750004463098])
    assert 'BOOTSTAP-DISTRIBUTIONS' in Result_1['Full Summary']
    
    #'Reservoir' Measurements are now Controls and 'Channel' measurements are Treatments
    #This does not use differential deformation in linmixmod()
    treatment2 = ['Treatment', 'Control', 'Treatment', 'Control',\
    'Treatment', 'Control','Treatment', 'Control']
    timeunit2 = [1, 1, 2, 2, 3, 3, 4, 4]
    Result_2 = linmixmod(xs=xs,treatment=treatment2,timeunit=timeunit2)
    assert np.allclose([Result_2["Estimate"]], [17.171341507432501])
    assert 'BOOTSTAP-DISTRIBUTIONS' not in Result_2['Full Summary']

def test_diffdef():
    xs = [
    [100,99,80,120,140,150,100,100,110,111,140,145], #Larger values (Channel1)
    [20,10,5,16,14,22,27,26,5,10,11,8,15,17,20,9]#Smaller values (Reservoir1)
    ]
    result = diffdef(xs[0],xs[1],Bootstrapiterations=1000)
    assert np.allclose([np.median(result[0])], [110.5])
    assert np.allclose([np.median(result[1])], [14.5])



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
loc[key]()
