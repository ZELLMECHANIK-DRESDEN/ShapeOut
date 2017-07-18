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

from helper_methods import retreive_session, cleanup


def setup_session_task(name):
    path = retreive_session(name)
    Arc = zipfile.ZipFile(path, mode='r')
    tempdir = tempfile.mkdtemp(prefix="ShapeOut-test_")
    Arc.extractall(tempdir)
    Arc.close()
    return tempdir, dirname(path)


def compatibility_task(name):
    tempdir, search_path = setup_session_task(name)
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


def test_070():
    analysis = compatibility_task("session_v0.7.0.zmso")
    mm = analysis.measurements[0]
    assert len(mm) == 44
    assert np.sum(mm._filter) == 12


def test_070hierarchy2():
    analysis = compatibility_task("session_v0.7.0_hierarchy2.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[2]._filter) == len(mms[2])
    assert np.sum(mms[1]._filter) == 13


def test_074ierarchy2():
    analysis = compatibility_task("session_v0.7.4_hierarchy2.zmso")
    
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[1]._filter) == 0


def test_075ierarchy1():
    analysis = compatibility_task("session_v0.7.5_hierarchy1.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == 19


def test_075ierarchy2():
    analysis = compatibility_task("session_v0.7.5_hierarchy2.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[0]._filter) == 17
    assert np.sum(mms[2]._filter) == 4


def test_076ierarchy2():
    analysis = compatibility_task("session_v0.7.6_hierarchy2.zmso")
    mms = analysis.measurements
    assert mms[3].title == "rtdc_data_traces_video - M1_child_child_child"
    assert len(mms[0]) == 44
    assert len(mms[1]) == 32
    assert len(mms[2]) == 12
    assert len(mms[3]) == 9


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



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
