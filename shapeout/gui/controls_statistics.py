#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - statistics display"""
from __future__ import division, print_function, unicode_literals

import wx
import wx.grid as gridlib

from .. import util
from .controls_subpanel import SubPanel


class SubPanelStatistics(SubPanel):
    def __init__(self, *args, **kwargs):
        SubPanel.__init__(self, *args, **kwargs)

    def _box_statistics(self, analysis):
        """
        Returns a wxBoxSizer with statistics information about
        each element in analysis.
        """
        sizer = wx.BoxSizer(wx.VERTICAL)

        if analysis is not None:
            colors = []
            for mm in analysis.measurements:
                colors.append(mm.config["plotting"]["contour color"])
            
            head, datalist = analysis.GetStatisticsBasic()
             
            myGrid = gridlib.Grid(self)
            myGrid.CreateGrid(len(datalist), len(head)-1)

            sizer.Add(myGrid, 1, wx.EXPAND)
            
            for ii, label in enumerate(head[1:]):
                myGrid.SetColLabelValue(ii, label)
                myGrid.SetColSize(ii, 10*len(label))

            for jj, row, color in zip(range(len(datalist)), datalist, colors):
                if analysis.GetParameters("plotting")["scatter title colored"]:
                    if isinstance(color, (list, tuple)):
                        color = util.rgb_to_hex(color[:3], norm=1)
                else:
                    color = "black"
                for ii, item in enumerate(row):
                    if isinstance(item, (str, unicode)):
                        label = u" {} ".format(item)
                    else:
                        label = u" {} ".format(util.float2string_nsf(item, n=3))
                    if ii is 0:
                        myGrid.SetRowLabelValue(jj, label)
                        oldsize = myGrid.GetRowLabelSize()
                        newsize = len(label)*10
                        myGrid.SetRowLabelSize(max(oldsize, newsize))
                    else:
                        myGrid.SetCellValue(jj, ii-1, label)
                        myGrid.SetCellTextColour(jj, ii-1, color)
                        myGrid.SetReadOnly(jj, ii-1)
            sizer.Layout()
        return sizer


    def UpdatePanel(self, analysis):
        """  """
        self.ClearSubPanel()
        # Create three boxes containing information
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        statbox = self._box_statistics(analysis)
        # same size 
        h = statbox.GetMinSize()[1]
        h = max(h, 50)
        statbox.SetMinSize((-1, h))
        sizer.Add(statbox)
        self.SetSizer(sizer)
        sizer.Fit(self)
