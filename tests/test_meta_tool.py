#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import os
import os.path as op
import tempfile

from dclab import new_dataset

from helper_methods import example_data_dict, retrieve_data, cleanup

from shapeout import meta_tool


def test_collect_data_tree():
    features = ["area_um", "deform", "time"]
    edest = tempfile.mkdtemp()

    for ii in range(1, 4):
        dat = new_dataset(data=example_data_dict(ii + 10, keys=features))
        cfg = {"experiment": {"sample": "test sample",
                              "run index": ii},
               "imaging": {"pixel size": 0.34},
               "setup": {"channel width": 20,
                         "chip region": "channel",
                         "flow rate": 0.04}
               }
        dat.config.update(cfg)
        dat.export.hdf5(path=op.join(edest, "{}.rtdc".format(ii)),
                        features=features)
    data = meta_tool.collect_data_tree([edest])[0]
    assert len(data) == 1, "only one data folder"
    assert len(data[0]) == 4, "three measurements"

    # check name
    assert data[0][0][0] == "test sample"

    # check order
    assert data[0][1][1].endswith("1.rtdc")
    assert data[0][2][1].endswith("2.rtdc")
    assert data[0][3][1].endswith("3.rtdc")


def test_hdf5():
    path = retrieve_data("rtdc_data_hdf5_contour_image_trace.zip")
    assert meta_tool.get_chip_region(path) == "channel"
    assert meta_tool.get_event_count(path) == 5
    assert meta_tool.get_flow_rate(path) == .16
    assert meta_tool.get_run_index(path) == 1
    assert meta_tool.get_sample_name(path) == "artificial test data"
    assert meta_tool.verify_dataset(path)
    cleanup()


def test_tdms():
    path = retrieve_data("rtdc_data_minimal.zip")
    assert meta_tool.get_chip_region(path) == "channel"
    assert meta_tool.get_event_count(path) == 156
    assert meta_tool.get_flow_rate(path) == .12
    assert meta_tool.get_run_index(path) == 1
    assert "rtdc_data_minimal.zip" in meta_tool.get_sample_name(path)
    assert meta_tool.verify_dataset(path)
    cleanup()


def test_tdms_avi():
    path = retrieve_data("rtdc_data_traces_video.zip")
    assert meta_tool.get_chip_region(path) == "channel"
    # this is the number of frames in the video file
    assert meta_tool.get_event_count(path) == 2
    assert meta_tool.get_flow_rate(path) == .16
    assert meta_tool.get_run_index(path) == 1
    assert "rtdc_data_traces_video.zip" in meta_tool.get_sample_name(path)
    assert meta_tool.verify_dataset(path)
    cleanup()


def test_tdms_avi2():
    path = retrieve_data("rtdc_data_traces_video.zip")
    # delete avi file  and get event count from tdms file
    os.remove(str(path.parent / "M1_imaq.avi"))
    assert meta_tool.verify_dataset(path)
    cleanup()


def test_verify():
    path = retrieve_data("rtdc_data_minimal.zip")
    os.remove(str(path.parent / "M1_camera.ini"))
    assert not meta_tool.verify_dataset(path)
    cleanup()


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
