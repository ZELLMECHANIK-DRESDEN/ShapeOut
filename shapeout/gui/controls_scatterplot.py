#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - scatter plot control panel"""
from __future__ import division, print_function, unicode_literals

import wx

from . import confparms
from .controls_subpanel import SubPanel


Plotting_Elements_Scatter = ["downsampl", "scatter"] # Downsampl [sic]


class SubPanelPlotScatter(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.key = "plotting"


    def _box_from_cfg_scatter(self, analysis):
        """ Top panel draw plotting elements
        """
        key = self.key
        
        mastersizer = wx.BoxSizer(wx.HORIZONTAL)

        scatter = wx.StaticBox(self, label="Parameters")
        scatterbox = wx.StaticBoxSizer(scatter, wx.VERTICAL)
        scattersizer = wx.BoxSizer(wx.VERTICAL)
        scatterbox.Add(scattersizer)
        mastersizer.Add(scatterbox)

        items = analysis.GetParameters(key).items()

        ## Scatter plot data
        items = confparms.SortConfigurationKeys(items)
        for item in items:
            for strid in Plotting_Elements_Scatter:
                if item[0].startswith(strid):
                    stemp = self._create_type_wx_controls(analysis, 
                                                          key, item)
                    scattersizer.Add(stemp)

        scatterbox.SetMinSize((-1, scatterbox.GetMinSize()[1]))

        scattersizer.Layout()
        mastersizer.Layout()
        
        return mastersizer


    def UpdatePanel(self, analysis):
        """Redraw the entire panel"""
        self.ClearSubPanel()

        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        fbox = self._box_from_cfg_scatter(analysis)
        sizer.Add(fbox)

        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label="Apply")
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangePlot, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label="Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        self.BindEnableName(ctrl_source="downsampling",
                            value=True,
                            ctrl_targets=["downsample events"])

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
