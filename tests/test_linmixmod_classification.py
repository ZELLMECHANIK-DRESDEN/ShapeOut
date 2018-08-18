#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import numpy as np

import dclab
from shapeout.analysis import Analysis
from shapeout.lin_mix_mod import match_similar_strings, \
    classify_treatment_repetition


def test_match_similar_strings_simple():
    a = ["peter", "hans", "", "golf"]
    b = ["gogo", "ham", "freddy", ""]
    c = [""] * 4
    d = [""] * 4
    ids = match_similar_strings(a, b, c, d)
    ids = [[m[0], m[1]] for m in ids]
    assert [1, 1] in ids
    assert [3, 0] in ids
    assert [0, 2] in ids


def test_match_similar_strings_advanced():
    a = ["peter", "hans", "", "golf"]
    b = ["gogo", "ham", "freddy", ""]
    c = ["red", "gans", "", "hugo"]
    d = ["old", "futur", "erst", "ha"]
    ids = match_similar_strings(a, b, c, d)
    assert [1, 1, 1, 3] in ids
    assert [3, 0, 3, 0] in ids
    assert [0, 2, 0, 2] in ids


def test_classify_treatment_repetition_simple():
    measurements = []
    dd = {"area_um": np.linspace(40, 50, 10),
          "deform": np.linspace(.1, .2, 10)}
    for ii in range(5):
        ctl = dclab.new_dataset(dd)
        ctl.title = "donor {} control".format(ii)
        ctl.config["setup"]["chip region"] = "channel"
        trt = dclab.new_dataset(dd)
        trt.title = "donor {}".format(ii)
        trt.config["setup"]["chip region"] = "channel"
        measurements += [ctl, trt]
    ana = Analysis(measurements)
    treatment, repetition = classify_treatment_repetition(ana, id_ctl="control")
    assert treatment == ["Control", "Treatment"] * 5
    assert np.all(repetition == np.repeat(np.arange(5), 2) + 1)


def test_classify_treatment_repetition_simple_2():
    measurements = []
    dd = {"area_um": np.linspace(40, 50, 10),
          "deform": np.linspace(.1, .2, 10)}
    for ii in range(5):
        ctl = dclab.new_dataset(dd)
        ctl.title = "donor {}".format(ii)
        ctl.config["setup"]["chip region"] = "channel"
        trt = dclab.new_dataset(dd)
        trt.title = "donor {} treatment".format(ii)
        trt.config["setup"]["chip region"] = "channel"
        measurements += [ctl, trt]
    ana = Analysis(measurements)
    treatment, repetition = classify_treatment_repetition(ana,
                                                          id_ctl="",
                                                          id_trt="treatment")
    assert treatment == ["Control", "Treatment"] * 5
    assert np.all(repetition == np.repeat(np.arange(5), 2) + 1)


def test_classify_treatment_repetition_advanced():
    measurements = []
    dd = {"area_um": np.linspace(40, 50, 10),
          "deform": np.linspace(.1, .2, 10)}
    for ii in range(12):
        ctl = dclab.new_dataset(dd)
        ctl.title = "donor {} control".format(ii)
        ctl.config["setup"]["chip region"] = "channel"

        trt = dclab.new_dataset(dd)
        trt.title = "donor {}".format(ii)
        trt.config["setup"]["chip region"] = "channel"

        ctlr = dclab.new_dataset(dd)
        ctlr.title = "donor {} control reservoir".format(ii)
        ctlr.config["setup"]["chip region"] = "reservoir"

        trtr = dclab.new_dataset(dd)
        trtr.title = "donor {} reservoir".format(ii)
        trtr.config["setup"]["chip region"] = "reservoir"

        measurements += [ctl, trt, ctlr, trtr]
    ana = Analysis(measurements)
    treatment, repetition = classify_treatment_repetition(
        ana,
        id_ctl="control",
        id_ctl_res="control reservoir",
        id_trt_res="reservoir")

    # Repetitions 1 and 2 are put in the end b/c "11" and "12" are better
    # matches than "1" and "2".
    repetition = np.roll(repetition, 8)
    assert treatment == ["Control",
                         "Treatment",
                         "Reservoir Control",
                         "Reservoir Treatment"] * 12
    assert np.all(repetition == np.repeat(np.arange(12), 4) + 1)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
