#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - contour control panel
"""
from __future__ import division, print_function

import numpy as np
import wx
import dclab

from .. import tlabwrap
from .controls_subpanel import SubPanel


# These lists name items that belong to separate pages, startsiwth(item)
Plotting_Elements_Contour = ["Contour", "KDE"]


class SubPanelPlotContour(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.key = "Plotting"


    def _box_from_cfg_contour(self, analysis):
        """ Top panel draw plotting elements
        """
        key = self.key
        
        mastersizer = wx.BoxSizer(wx.HORIZONTAL)

        contour = wx.StaticBox(self, label=_("Parameters"))
        contourbox = wx.StaticBoxSizer(contour, wx.VERTICAL)
        contoursizer = wx.BoxSizer(wx.VERTICAL)
        contourbox.Add(contoursizer)
        mastersizer.Add(contourbox)

        items = analysis.GetParameters(key).items()
        # Remove individual contour color
        for item in items:
            if item[0] == "Contour Color":
                items.remove(item)
        
        # Remove all items that have nothing to do with plotting
        xax, yax = analysis.GetPlotAxes()
        for topic in ["KDE Multivariate", "Contour Accuracy"]:
            dellist = list()
            for item in items:
                if (item[0].startswith(topic) and
                   not (item[0].endswith(xax) or item[0].endswith(yax))):
                    dellist.append(item)
            for it in dellist:
                items.remove(it)

        ## Contour plot data
        items = tlabwrap.SortConfigurationKeys(items)
        for item in items:
            for strid in Plotting_Elements_Contour:
                if item[0].startswith(strid):
                    stemp = self._create_type_wx_controls(analysis, 
                                                          key, item)
                    contoursizer.Add(stemp)

        ## Color and name selection
        # ["Plotting"]["Contour Color"] and
        # mm.title
        titlecol = wx.StaticBox(self, label=_("Titles and Colors"))
        titlecolbox = wx.StaticBoxSizer(titlecol, wx.VERTICAL)
        titlecolsizer = wx.BoxSizer(wx.VERTICAL)
        titlecolbox.Add(titlecolsizer)
        mastersizer.Add(titlecolbox)
        
        for mm in analysis.measurements:
            shor = wx.BoxSizer(wx.HORIZONTAL)
            # title
            tit = wx.TextCtrl(self, value=str(mm.title), size=(300, -1),
                            name="Title "+mm.identifier)
            # color
            color = mm.Configuration["Plotting"]["Contour Color"]
            # convert tuple to wxColour
            if isinstance(color, list):
                color=wx.Colour(*np.array(color)*255)
            col = wx.ColourPickerCtrl(self, name="Color "+mm.identifier,
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
        """  """
        self.ClearSubPanel()
        
        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        fbox = self._box_from_cfg_contour(analysis)
        sizer.Add(fbox)

        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label=_("Apply"))
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangePlot, btn_apply)
        vertsizer.Add(btn_apply)
        
        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)
        
        axes = analysis.GetPlotAxes()
        self.BindEnableName(ctrl_source="KDE",
                            value="Multivariate",
                            ctrl_targets=["KDE Multivariate {}".format(a) for a in axes])

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
