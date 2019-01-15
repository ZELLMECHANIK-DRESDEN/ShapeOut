#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test gui session"""
from __future__ import print_function

from os.path import abspath, dirname
import sys

import io
import tempfile

import numpy as np
import unittest

import dclab


# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from shapeout.__main__ import prepare_app

from helper_methods import retreive_session, cleanup


class TestSimple(unittest.TestCase):
    '''Test Shape-Out session'''

    def setUp(self):
        '''Create the GUI'''
        self.app = prepare_app()
        self.frame = self.app.frame
        # self.frame.InitRun()

    def tearDown(self):
        cleanup()

    def test_075ierarchy2(self):
        zsmo = retreive_session("session_v0.7.5_hierarchy2.zmso")
        self.frame.OnMenuLoad(session_file=zsmo)
        mms = self.frame.analysis.measurements
        assert np.sum(mms[0]._filter) == len(mms[1])
        assert np.sum(mms[1]._filter) == len(mms[2])
        assert np.sum(mms[0]._filter) == 17
        assert np.sum(mms[2]._filter) == 4


if __name__ == "__main__":
    unittest.main()
