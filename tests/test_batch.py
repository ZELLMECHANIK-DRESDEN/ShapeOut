#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test batch control
"""
from __future__ import print_function

from os.path import abspath, dirname
import sys

import unittest
import dclab
import tempfile

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from shapeout.__main__ import prepare_app

from helper_methods import retreive_tdms, example_data_sets


class TestSimple(unittest.TestCase):
    '''Test the PyJibe mixer GUI'''
    def setUp(self):
        '''Create the GUI'''
        self.app = prepare_app()
        self.frame = self.app.frame
        #self.frame.InitRun()
    
    def test_batch(self):
        # load data
        tdms_path = retreive_tdms(example_data_sets[0])
        ds = dclab.RTDC_DataSet(tdms_path=tdms_path)
        #anal = shapeout.analysis.Analysis()
        # start session
        self.frame.NewAnalysis([ds])
        batch = self.frame.OnMenuBatchFolder()
        batch.out_tsv_file=tempfile.mkstemp(".tsv", "shapeout_batch")[1]
        batch.tdms_files=[tdms_path]
        batch.OnBatch()


if __name__ == "__main__":
    unittest.main()