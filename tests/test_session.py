#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

from os.path import abspath, dirname
import sys
import unittest

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from shapeout.__main__ import prepare_app

from helper_methods import retreive_session, cleanup


class TestFiles(unittest.TestCase):
    '''Test ShapeOut batch'''
    def setUp(self):
        '''Create the GUI'''
        self.app = prepare_app()
        self.frame = self.app.frame
        #self.frame.InitRun()

    def test_060(self):
        zsmofile = retreive_session("session_v0.6.0.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mm = self.frame.analysis.measurements[0]
        assert len(mm) == 44
        assert np.sum(mm._filter) == 12
        cleanup()


    def test_065(self):
        zsmofile = retreive_session("session_v0.6.5.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mm = self.frame.analysis.measurements[0]
        assert len(mm) == 44
        assert np.sum(mm._filter) == 22
        cleanup()


    def test_070(self):
        zsmofile = retreive_session("session_v0.7.0.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mm = self.frame.analysis.measurements[0]
        assert len(mm) == 44
        assert np.sum(mm._filter) == 12
        cleanup()


    def test_070hierarchy2(self):
        zsmofile = retreive_session("session_v0.7.0_hierarchy2.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mms = self.frame.analysis.measurements
        assert np.sum(mms[0]._filter) == len(mms[1])
        assert np.sum(mms[1]._filter) == len(mms[2])
        assert np.sum(mms[2]._filter) == len(mms[2])
        assert np.sum(mms[1]._filter) == 13
        cleanup()


    def test_074ierarchy2(self):
        zsmofile = retreive_session("session_v0.7.4_hierarchy2.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mms = self.frame.analysis.measurements
        assert np.sum(mms[0]._filter) == len(mms[1])
        assert np.sum(mms[1]._filter) == len(mms[2])
        assert np.sum(mms[1]._filter) == 0
        cleanup()


    def test_075ierarchy1(self):
        zsmofile = retreive_session("session_v0.7.5_hierarchy1.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mms = self.frame.analysis.measurements
        assert np.sum(mms[0]._filter) == len(mms[1])
        assert np.sum(mms[1]._filter) == 19
        cleanup()


    def test_075ierarchy2(self):
        zsmofile = retreive_session("session_v0.7.5_hierarchy2.zmso")
        self.frame.OnMenuLoad(session_file=zsmofile)
        mms = self.frame.analysis.measurements
        assert np.sum(mms[0]._filter) == len(mms[1])
        assert np.sum(mms[1]._filter) == len(mms[2])
        assert np.sum(mms[0]._filter) == 17
        assert np.sum(mms[2]._filter) == 4
        cleanup()


if __name__ == "__main__":
    unittest.main()
