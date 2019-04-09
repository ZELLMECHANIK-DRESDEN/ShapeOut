#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - contour control panel"""
from __future__ import division, print_function, unicode_literals

import pathlib

import numpy as np
import wx

from . import confparms
from .controls_subpanel import SubPanel


# These lists name items that belong to separate pages, startsiwth(item)
Plotting_Elements_Contour = ["contour", "kde"]


class SubPanelPlotContour(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.key = "plotting"


    def _box_from_cfg_contour(self, analysis):
        """ Top panel draw plotting elements
        """
        key = self.key
        
        mastersizer = wx.BoxSizer(wx.HORIZONTAL)

        contour = wx.StaticBox(self, label="Parameters")
        contourbox = wx.StaticBoxSizer(contour, wx.VERTICAL)
        contoursizer = wx.BoxSizer(wx.VERTICAL)
        contourbox.Add(contoursizer)
        mastersizer.Add(contourbox)

        items = analysis.GetParameters(key).items()
        # Remove individual contour color
        for item in items:
            if item[0] == "contour color":
                items.remove(item)
        
        # Remove all items that have nothing to do with plotting
        xax, yax = analysis.GetPlotAxes()
        for topic in ["kde accuracy", "contour accuracy"]:
            dellist = []
            for item in items:
                # item: e.g. ("kde accuracy fl2area", 1000)
                if item[0].startswith(topic):
                    # e.g. fl2area
                    rest = item[0][len(topic):].strip()
                    if not (rest==xax or rest==yax):
                        # only keep the indices that we need
                        dellist.append(item)
            for it in dellist:
                items.remove(it)

        ## Contour plot data
        items = confparms.SortConfigurationKeys(items)
        for item in items:
            for strid in Plotting_Elements_Contour:
                if item[0].startswith(strid):
                    stemp = self._create_type_wx_controls(analysis, 
                                                          key, item)
                    contoursizer.Add(stemp)

        ## Color and name selection
        # ["Plotting"]["Contour Color"] and
        # mm.title
        titlecol = wx.StaticBox(self, label="Titles and Colors")
        titlecolbox = wx.StaticBoxSizer(titlecol, wx.VERTICAL)
        titlecolsizer = wx.BoxSizer(wx.VERTICAL)
        titlecolbox.Add(titlecolsizer)
        mastersizer.Add(titlecolbox)
        
        for mm in analysis.measurements:
            shor = wx.BoxSizer(wx.HORIZONTAL)
            # title
            tit = wx.TextCtrl(self, value=str(mm.title), size=(300, -1),
                              name="title "+mm.identifier)
            tit.SetToolTip(wx.ToolTip(path2str(mm.path)))
            # color
            color = mm.config["plotting"]["contour color"]
            # convert tuple to wxColour
            if isinstance(color, list):
                color=wx.Colour(*np.array(color)*255)
            col = wx.ColourPickerCtrl(self, name="color "+mm.identifier,
                                      col=color)
            shor.Add(col)
            shor.Add(tit)
            titlecolsizer.Add(shor)

        contourbox.SetMinSize((-1, contourbox.GetMinSize()[1]))
        contoursizer.Layout()
        titlecolsizer.Layout()
        mastersizer.Layout()
        
        return mastersizer


    def UpdatePanel(self, analysis):
        self.ClearSubPanel()
        
        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        fbox = self._box_from_cfg_contour(analysis)
        sizer.Add(fbox)

        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label="Apply")
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangePlot, btn_apply)
        vertsizer.Add(btn_apply)
        
        btn_reset = wx.Button(self, label="Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)
        
        axes = analysis.GetPlotAxes()
        self.BindEnableName(ctrl_source="kde",
                            value=["multivariate", "histogram"],
                            ctrl_targets=["kde accuracy {}".format(a) for a in axes])
        self.SetSizer(sizer)
        sizer.Fit(self)


def path2str(path):
    """Safely convert a path to a string"""
    if isinstance(path, pathlib.Path):
        path = path.as_uri()
    return path
