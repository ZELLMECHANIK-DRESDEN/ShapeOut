#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import os

import numpy as np

from helper_methods import retrieve_data, cleanup

from shapeout import meta_tool


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
