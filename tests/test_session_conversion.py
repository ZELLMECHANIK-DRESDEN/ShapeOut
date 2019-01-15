#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import numpy as np

from shapeout.session import index, rw
from shapeout.analysis import Analysis

from helper_methods import cleanup, extract_session


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


def test_074hierarchy2():
    analysis = compatibility_task("session_v0.7.4_hierarchy2.zmso")

    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[1]._filter) == 0
    cleanup()


def test_075hierarchy1():
    analysis = compatibility_task("session_v0.7.5_hierarchy1.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == 19
    cleanup()


def test_075hierarchy2():
    analysis = compatibility_task("session_v0.7.5_hierarchy2.zmso")
    mms = analysis.measurements
    assert np.sum(mms[0]._filter) == len(mms[1])
    assert np.sum(mms[1]._filter) == len(mms[2])
    assert np.sum(mms[0]._filter) == 17
    assert np.sum(mms[2]._filter) == 4
    cleanup()


def test_076hierarchy2():
    analysis = compatibility_task("session_v0.7.6_hierarchy2.zmso")
    mms = analysis.measurements
    assert mms[3].title == "rtdc_data_traces_video - M1_child_child_child"
    assert len(mms[0]) == 44
    assert len(mms[1]) == 32
    assert len(mms[2]) == 12
    assert len(mms[3]) == 9
    cleanup()


def test_077hierarchy2():
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


def test_078hierarchy2():
    """
    In 0.7.8, each dataset gets a unique identifier that is independent
    of the data it holds. Therefore, two identical datasets (same filters,
    same hierarchy parents) will always have a different identifier. 
    """
    analysis = compatibility_task("session_v0.7.8_hierarchy2.zmso")
    mms = analysis.measurements
    assert mms[0].title == "parent"
    assert mms[1].title == "child1"
    assert mms[2].title == "child2"
    assert mms[3].title == "grandchild1a"
    assert mms[4].title == "grandchild1b"
    assert mms[5].title == "grandchild2a"
    assert len(mms[0]) == 44
    assert len(mms[1]) == 37
    assert len(mms[2]) == 37
    assert len(mms[3]) == 22
    assert len(mms[4]) == 22
    assert len(mms[5]) == 15
    assert mms[0].identifier == "mm-tdms_8a43345"
    assert mms[1].identifier == "mm-hierarchy_b7a2c21"
    assert mms[2].identifier == "mm-hierarchy_bbcb5a8"
    assert mms[3].identifier == "mm-hierarchy_4c7d883"
    assert mms[4].identifier == "mm-hierarchy_91b0b96"
    assert mms[5].identifier == "mm-hierarchy_38d374e"
    cleanup()


def test_078inertratio():
    """
    In dclab commit 41bf38e74e4d7dbf25c7d4c37214674b7ea242d6, the column
    "inert_ratio" was renamed to "inert_ratio_cvx". The conversion of the
    corresponding session config values is done starting Shape-Out 0.7.9.
    """
    analysis = compatibility_task("session_v0.7.8_hierarchy2.zmso")
    mms = analysis.measurements
    assert "inert_ratio_cvx min" in mms[0].config["filtering"]
    assert "inert_ratio_cvx max" in mms[0].config["filtering"]
    assert "inert_ratio_raw min" in mms[0].config["filtering"]
    assert "inert_ratio_raw max" in mms[0].config["filtering"]
    assert "inert_ratio min" not in mms[0].config["filtering"]
    assert "inert_ratio max" not in mms[0].config["filtering"]
    cleanup()


def test_080():
    """Major version test
    """
    analysis = compatibility_task("session_v0.8.0.zmso")
    mms = analysis.measurements
    assert mms[0].title == 'rtdc_data_traces_video - M1'
    assert mms[-1].title == 'rtdc_data_traces_video - M1_child_child'
    assert len(mms[-1]) == 3
    assert len(mms) == 5
    assert mms[0].config["plotting"]["axis y"] == "volume"
    cleanup()


def test_083():
    """Major version test
    """
    analysis = compatibility_task("session_v0.8.3.zmso")
    mms = analysis.measurements
    mm = mms[0]
    assert len(mm) == 44
    assert np.sum(mm.filter.all) == 30
    # In the configuration file, this is set to "False" by accident.
    assert mm.config["filtering"]["limit events"] == 0
    cleanup()


def test_084_pre_isoelastics_conversion():
    """Manual filters for hierarchy children are stored in session
    """
    analysis = compatibility_task("session_v0.7.5_hierarchy2.zmso")
    mms = analysis.measurements
    # isoelastics = True
    assert mms[0].config["plotting"]["isoelastics"] == "legacy"

    analysis = compatibility_task("session_v0.8.0.zmso")
    mms = analysis.measurements
    # isoelastics = False
    assert mms[0].config["plotting"]["isoelastics"] == "not shown"

    cleanup()


def test_084_manhierarchy():
    """Manual filters for hierarchy children are stored in session
    """
    analysis = compatibility_task("session_v0.8.4_hierarchy_filtman.zmso")
    mms = analysis.measurements
    assert mms[0].title == '0000_SessionTest - M1'
    assert mms[1].title == '0000_SessionTest - M1_child'
    # check basic filter settings
    assert len(mms[1]) == 37
    assert not mms[1].filter.manual[26]
    # make hidden manual filter visible
    mms[0].config["filtering"]["enable filters"] = False
    mms[1].apply_filter()
    assert len(mms[1]) == 44
    assert not mms[1].filter.manual[7]
    assert not mms[1].filter.manual[32]
    cleanup()


def test_086_removed_keys_dclab034():
    """Removed keys in dclab 0.3.4"""
    analysis = compatibility_task("session_v0.8.4_hierarchy_filtman.zmso")
    mm = analysis.measurements[0]
    # changed configs
    assert "temperature" not in mm.config["setup"]
    assert "viscosity" not in mm.config["setup"]
    assert "exposure time" not in mm.config["imaging"]
    assert "flash current" not in mm.config["imaging"]
    # renamed column "ncells" to "nevents"
    assert "ncells max" not in mm.config["filtering"]
    assert "nevents max" in mm.config["filtering"]


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
