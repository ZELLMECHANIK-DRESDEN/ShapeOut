#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

from os.path import abspath, dirname, join
import sys
import tempfile
import zipfile

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from shapeout.session import conversion, index, rw
from shapeout.analysis import Analysis

from helper_methods import cleanup, extract_session, retreive_session


def compatibility_task(name):
    tempdir, search_path = extract_session(name)
    rtdc_list = rw.load(tempdir, search_path=search_path)
    idout = index.index_check(tempdir, search_path=search_path)
    assert len(idout["missing files"]) == 0
    analysis = Analysis(rtdc_list)
    return analysis
    

def test_060():
    analysis = compatibility_task("session_v0.6.0.zmso")
    mm = analysis.measurements[0]
    assert len(mm) == 44
    assert np.sum(mm._filter) == 12
    cleanup()


def test_065():
    analysis = compatibility_task("session_v0.6.5.zmso")
    mm = analysis.measurements[0]
    assert len(mm) == 44
    assert np.sum(mm._filter) == 22
    cleanup()


def test_070():
    analysis = compatibility_task("session_v0.7.0.zmso")
    mm = analysis.measurements[0]
    assert len(mm) == 44
    assert np.sum(mm._filter) == 12
    cleanup()


def test_070hierarchy2():
    analysis = compatibility_task("session_v0.7.0_hierarchy2.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[2]._filter) == len(mms[2])
    assert np.sum(mms[1]._filter) == 13
    cleanup()


def test_074ierarchy2():
    analysis = compatibility_task("session_v0.7.4_hierarchy2.zmso")
    
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[1]._filter) == 0
    cleanup()


def test_075ierarchy1():
    analysis = compatibility_task("session_v0.7.5_hierarchy1.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == 19
    cleanup()


def test_075ierarchy2():
    analysis = compatibility_task("session_v0.7.5_hierarchy2.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[0]._filter) == 17
    assert np.sum(mms[2]._filter) == 4
    cleanup()


def test_076ierarchy2():
    analysis = compatibility_task("session_v0.7.6_hierarchy2.zmso")
    mms = analysis.measurements
    assert mms[3].title == "rtdc_data_traces_video - M1_child_child_child"
    assert len(mms[0]) == 44
    assert len(mms[1]) == 32
    assert len(mms[2]) == 12
    assert len(mms[3]) == 9
    cleanup()


def test_077ierarchy2():
    analysis = compatibility_task("session_v0.7.7_hierarchy2.zmso")
    mms = analysis.measurements
    assert mms[0].title == "original data"
    assert mms[1].title == "child1"
    assert mms[2].title == "grandchild1a"
    assert mms[3].title == "child2"
    assert mms[4].title == "grandchild2a"
    assert len(mms[0]) == 44
    assert len(mms[1]) == 37
    assert len(mms[2]) == 14
    assert len(mms[3]) == 37
    assert len(mms[4]) == 19
    # Backwards compatibility: identifiers are saved in session and not anymore
    # computed from session hashes in 0.7.8. Using the `key` of the measurement
    # allows to assign new unique identifiers.
    assert mms[0].identifier == "1_mm-tdms_92601489292dc9bf9fc040f87d9169c0"
    assert mms[1].identifier == "2_mm-hierarchy_033dc4bc9d581bcfcdb9f153105f3b15"
    assert mms[2].identifier == "3_mm-hierarchy_119eb293afc12ad63c4b8f8db962d0e3"
    assert mms[3].identifier == "4_mm-hierarchy_c30bc68d7339267d61c2e0382ae8ba26"
    assert mms[4].identifier == "5_mm-hierarchy_3bed98d737cd70f1c46d5ab44cb627a8"
    cleanup()



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()