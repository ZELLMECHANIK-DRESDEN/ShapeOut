#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
For this test to work, this must be installed
 
 - Python package pyper
 - R-base
 - R package 'lme4'
"""
from __future__ import division, print_function, unicode_literals

import copy

import numpy as np

from shapeout.lin_mix_mod import linmixmod, diffdef


xs = [
    [100, 99, 80, 120, 140, 150, 100, 100, 110, 111,
        140, 145],  # Larger values (Control Channel1)
    [20, 10, 5, 16, 14, 22, 27, 26, 5, 10, 11, 8, 15, 17,
        20, 9],  # Smaller values (Control Reservoir1)
    [115, 110, 90, 110, 145, 155, 110, 120, 115, 120, 120,
        150, 100, 90, 100],  # Larger values (Control Channel2)
    [30, 30, 15, 26, 24, 32, 37, 36, 15, 20, 21, 18, 25,
        27, 30, 19],  # Smaller values (Control Reservoir2)
    [150, 150, 130, 170, 190, 250, 150, 150, 160, 161, 180, 195, 130,
        120, 125, 130, 125],  # Larger values (Treatment Channel1)
    [2, 1, 5, 6, 4, 2, 7, 6, 5, 10, 1, 8, 5, 7, 2, 9, 11,
        8, 13],  # Smaller values (Treatment Reservoir1)
    [155, 155, 135, 175, 195, 255, 155, 155, 165, 165, 185, 200, 135, 125,
        130, 135, 140, 150, 135, 140],  # Larger values (Treatment Channel2)
    [25, 15, 19, 26, 44, 42, 35, 20, 15, 10, 11, 28, 35, 10, 25, 13]]  # Smaller values (Treatment Reservoir2)


def test_linmixmod_1():
    # 1.: Differential Deformation in a linear mixed model
    treatment1 = ['Control', 'Reservoir Control', 'Control', 'Reservoir Control',
                  'Treatment', 'Reservoir Treatment', 'Treatment', 'Reservoir Treatment']
    timeunit1 = [1, 1, 2, 2, 1, 1, 2, 2]
    Result_1 = linmixmod(xs=xs, treatment=treatment1,
                         timeunit=timeunit1, model='lmm')
    assert np.allclose([Result_1["Estimate"]], [93.693750004463098])
    assert 'BOOTSTAP-DISTRIBUTIONS' in Result_1['Full Summary']
    assert 'GENERALIZED' not in Result_1['Full Summary']
    assert np.allclose(
        [Result_1["p-Value (Likelihood Ratio Test)"]], [0.000602622503360039])


def test_linmixmod_2():
    # 2.: Differential Deformation in a generalized linear mixed model
    treatment2 = ['Control', 'Reservoir Control', 'Control', 'Reservoir Control',
                  'Treatment', 'Reservoir Treatment', 'Treatment', 'Reservoir Treatment']
    timeunit2 = [1, 1, 2, 2, 1, 1, 2, 2]
    Result_2 = linmixmod(xs=xs, treatment=treatment2,
                         timeunit=timeunit2, model='glmm')
    assert np.allclose([Result_2["Estimate"]], [4.5385848573783898])
    assert 'BOOTSTAP-DISTRIBUTIONS' in Result_2['Full Summary']
    assert 'GENERALIZED' in Result_2['Full Summary']
    assert np.allclose(
        [Result_2["p-Value (Likelihood Ratio Test)"]], [0.000556063024310929])


def test_linmixmod_3():
    # 3.: Original values in a linear mixed model
    #'Reservoir' Measurements are now Controls and 'Channel' measurements are Treatments
    # This does not use differential deformation in linmixmod()
    treatment3 = ['Treatment', 'Control', 'Treatment', 'Control',
                  'Treatment', 'Control', 'Treatment', 'Control']
    timeunit3 = [1, 1, 2, 2, 3, 3, 4, 4]
    Result_3 = linmixmod(xs=xs, treatment=treatment3,
                         timeunit=timeunit3, model='lmm')
    assert np.allclose([Result_3["Estimate"]], [17.171341507432501])
    assert 'BOOTSTAP-DISTRIBUTIONS' not in Result_3['Full Summary']
    assert 'GENERALIZED' not in Result_3['Full Summary']
    assert np.allclose(
        [Result_3["p-Value (Likelihood Ratio Test)"]], [0.000331343267412872])


def test_linmixmod_4():
    # 4.: Original values in a generalized linear mixed model
    # This does not use differential deformation in linmixmod()
    treatment4 = ['Treatment', 'Control', 'Treatment', 'Control',
                  'Treatment', 'Control', 'Treatment', 'Control']
    timeunit4 = [1, 1, 2, 2, 3, 3, 4, 4]
    Result_4 = linmixmod(xs=xs, treatment=treatment4,
                         timeunit=timeunit4, model='glmm')
    assert np.allclose([Result_4["Estimate"]], [2.71362344639])
    assert 'BOOTSTAP-DISTRIBUTIONS' not in Result_4['Full Summary']
    assert 'GENERALIZED' in Result_4['Full Summary']
    assert np.allclose(
        [Result_4["p-Value (Likelihood Ratio Test)"]], [0.00365675950677214])


def test_linmixmod_5():
    # 5.: Add None values and get same result as in 4.
    treatment5 = ['Treatment', 'Control', 'Treatment', 'Control',
                  'None', 'Treatment', 'Control', 'Treatment', 'Control']
    timeunit5 = [1, 1, 2, 2, 1, 3, 3, 4, 4]
    xs2 = copy.deepcopy(xs)
    xs2.insert(4, xs[0])
    Result_5 = linmixmod(xs=xs2, treatment=treatment5,
                         timeunit=timeunit5, model='glmm')
    assert np.allclose([Result_5["Estimate"]], [2.71362344639])
    assert 'BOOTSTAP-DISTRIBUTIONS' not in Result_5['Full Summary']
    assert 'GENERALIZED' in Result_5['Full Summary']
    assert np.allclose(
        [Result_5["p-Value (Likelihood Ratio Test)"]], [0.00365675950677214])


def test_linmixmod_6():
    # 6.: Same as 5, but with "0" timeuint instead of "None" treatment
    treatment6 = ['Treatment', 'Control', 'Treatment', 'Control',
                  'Treatment', 'Treatment', 'Control', 'Treatment', 'Control']
    timeunit6 = [1, 1, 2, 2, 0, 3, 3, 4, 4]
    xs2 = copy.deepcopy(xs)
    xs2.insert(4, xs[0])
    Result_6 = linmixmod(xs=xs2, treatment=treatment6,
                         timeunit=timeunit6, model='glmm')
    assert np.allclose([Result_6["Estimate"]], [2.71362344639])
    assert 'BOOTSTAP-DISTRIBUTIONS' not in Result_6['Full Summary']
    assert 'GENERALIZED' in Result_6['Full Summary']
    assert np.allclose(
        [Result_6["p-Value (Likelihood Ratio Test)"]], [0.00365675950677214])


def test_diffdef():
    # Larger values (Channel1)
    y = np.array([100, 99, 80, 120, 140, 150, 100, 100, 110, 111, 140, 145])
    # Smaller values (Reservoir1)
    yR = np.array([20, 10, 5, 16, 14, 22, 27, 26, 5, 10, 11, 8, 15, 17, 20, 9])
    result = diffdef(y, yR, bs_iter=1000)
    assert np.allclose([np.median(result[0])], [110.5])
    assert np.allclose([np.median(result[1])], [14.5])


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
