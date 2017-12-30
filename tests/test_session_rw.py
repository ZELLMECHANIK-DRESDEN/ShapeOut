#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
import tempfile

from shapeout.session import rw
from shapeout.analysis import Analysis

from helper_methods import cleanup, retrieve_data


def test_rw_basic():
    # Create a session with a few datasets
    f1 = retrieve_data("rtdc_data_traces_video.zip")
    f2 = retrieve_data("rtdc_data_minimal.zip")
    an = Analysis([f1, f2])
    msave = an.measurements
    _fd, fsave = tempfile.mkstemp(
        suffix=".zsmo", prefix="shapeout_test_session_")
    rw.save(path=fsave,
            rtdc_list=msave)
    mload = rw.load(fsave)

    assert mload[0].identifier == msave[0].identifier
    assert mload[1].identifier == msave[1].identifier

    cleanup()
    try:
        os.remove(fsave)
    except OSError:
        pass


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
