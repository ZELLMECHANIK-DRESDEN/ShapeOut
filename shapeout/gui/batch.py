#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - classes and methods for batch processing

"""
from __future__ import division, print_function

import numpy as np
import os
import wx
from wx.lib.scrolledpanel import ScrolledPanel

import dclab
from .. import tlabwrap


class BatchFilterFolder(wx.Frame):
    def __init__(self, parent, analysis):
        self.parent = parent
        self.analysis = analysis
        self.axes_panel_sizer = None
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title=_("Batch filtering"),
                          pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## panel
        panel = self.panel = wx.Panel(self)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        # init
        self.topSizer.Add(
            wx.StaticText(panel,
            label=_("Applies one filter to all measurements within a folder."))
            )
        self.topSizer.AddSpacer(10)
        ## Filter source selection
        boxleft = wx.StaticBox(panel, label=_("Filter settings"))
        self.rbtnhere = wx.RadioButton(panel, -1, 'Current session', 
                                        style = wx.RB_GROUP)
        self.rbtnhere.SetValue(True)
        self.rbtnthere = wx.RadioButton(panel, -1, 'Other source')
        self.rbtnthere.Disable()
        self.dropdown = wx.ComboBox(panel, -1, "", (15, 30),
                         wx.DefaultSize, [], wx.CB_DROPDOWN|wx.CB_READONLY)
        # Create the dropdownlist
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioHere, self.rbtnhere)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioThere, self.rbtnthere)
        self.Bind(wx.EVT_COMBOBOX, self.OnUpdateAxes, self.dropdown)
        leftSizer = wx.StaticBoxSizer(boxleft, wx.VERTICAL)
        leftSizer.Add(self.rbtnhere)
        leftSizer.Add(self.rbtnthere)
        leftSizer.AddSpacer(5)
        leftSizer.Add(self.dropdown)
        leftSizer.AddSpacer(5)
        self.topSizer.Add(leftSizer, 0, wx.EXPAND)

        ## Folder selection
        boxfold = wx.StaticBox(panel, label=_("Input folder"))
        foldSizer = wx.StaticBoxSizer(boxfold, wx.VERTICAL)
        btnbrws = wx.Button(panel, wx.ID_ANY, _("Browse"))
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, btnbrws)
        self.WXfold_text1 = wx.StaticText(panel,
                                          label="Please select a folder.")
        self.WXfold_text2 = wx.StaticText(panel, label="")
        fold2sizer = wx.BoxSizer(wx.HORIZONTAL)
        fold2sizer.Add(btnbrws)
        fold2sizer.Add(self.WXfold_text1, 0,
                       wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        foldSizer.AddSpacer(5)
        foldSizer.Add(fold2sizer, 0,
                      wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        foldSizer.Add(self.WXfold_text2, 0, wx.EXPAND)
        self.topSizer.Add(foldSizer, 0, wx.EXPAND)

        ## Axes checkboxes
        self.axes_panel = ScrolledPanel(panel, -1, size=(-1,200))
        self.axes_panel.SetupScrolling()
        self.topSizer.Add(self.axes_panel, 1, wx.EXPAND)

        self.topSizer.AddSpacer(15)

        ## Statistical parameters
        self.stat_panel = ScrolledPanel(panel, -1, size=(-1,200))
        self.stat_panel.SetupScrolling()
        self.topSizer.Add(self.stat_panel, 1, wx.EXPAND)
        self.SetupStatisticalParameters()

        ## Batch button
        btnbatch = wx.Button(self.panel, wx.ID_ANY, _("Perform batch filtering"))
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBatch, btnbatch)
        self.topSizer.Add(btnbatch, 0, wx.EXPAND)
        btnbatch.Disable()
        self.btnbatch = btnbatch

        panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self.panel)
        self.SetMinSize(self.topSizer.GetMinSizeTuple())

        self.OnRadioHere()
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)


    def OnBatch(self, e=None):
        # TODO:
        pass


    def OnBrowse(self, e=None):
        """ Let the user select a directory and search that directory
        for RT-DC data sets.
        """
        # make directory dialog
        dlg2 = wx.DirDialog(self,
                message=_("Please select directory containing measuremetns"),
                defaultPath=self.parent.config.GetWorkingDirectory("BatchFD"),
                style=wx.DD_DEFAULT_STYLE)
        
        if dlg2.ShowModal() == wx.ID_OK:
            thepath = dlg2.GetPath()
            self.WXfold_text1.SetLabel(thepath)
            self.parent.config.SetWorkingDirectory(thepath, "BatchFD")
            # Search directory
            wx.BeginBusyCursor()
            tree, _cols = tlabwrap.GetTDMSTreeGUI(thepath)
            wx.EndBusyCursor()
            self.WXfold_text2.SetLabel(_("Found {} measurements.").
                                       format(len(tree[0][0])))
            self.measurements = tree[0][0]
            self.btnbatch.Enable()

    
    def OnRadioHere(self, e=None):
        meas = [ mm.title for mm in self.analysis.measurements ]
        self.dropdown.SetItems(meas)
        self.dropdown.SetSelection(0)
        self.OnUpdateAxes()
        

    def OnRadioThere(self, e=None):
        print("there")
        self.OnUpdateAxes()
        
    
    def OnUpdateAxes(self, e=None):
        ## Remove initial stuff
        sizer = self.axes_panel_sizer
        panel = self.axes_panel
        if sizer is not None:
            for child in sizer.GetChildren():
                window = child.GetWindow()
                panel.RemoveChild(window)
                sizer.RemoveWindow(window)
                window.Destroy()
            sizerin = sizer
        else:
            box = wx.StaticBox(self.axes_panel, label=_("Data axes"))
            sizerin = wx.StaticBoxSizer(box, wx.VERTICAL)
            
        checks = []
        if self.rbtnhere.Value:
            sel = self.dropdown.GetSelection()
            mm = self.analysis.measurements[sel]
            for c in tlabwrap.dfn.rdv:
                if np.sum(np.abs(getattr(mm, c))):
                    checks.append(tlabwrap.dfn.cfgmap[c])
        else:
            for c in tlabwrap.dfn.rdv:
                checks.append(tlabwrap.dfn.cfgmap[c])

        checks = list(set(checks))
        labels = [ tlabwrap.dfn.axlabels[c] for c in checks ]

        # Sort checks according to labels
        checks = [x for (_y,x) in sorted(zip(labels,checks))]
        labels.sort()

        for c,l in zip(checks, labels):
            # label id (b/c of sorting)
            label = l
            cb = wx.CheckBox(self.axes_panel, label=_(label), name=c)
            sizerin.Add(cb)
            if c in self.analysis.GetPlotAxes():
                cb.SetValue(True)
        
        self.axes_panel.SetupScrolling()
        self.axes_panel.SetSizer(sizerin)
        sizerin.Fit(self.axes_panel)
        self.axes_panel_sizer=sizerin
        self.topSizer.Fit(self.panel)
        size=self.topSizer.GetMinSizeTuple()
        self.SetSize((size[0]+1, -1))
        self.SetSize((size[0]-1, -1))


    def SetupStatisticalParameters(self, e=None):
        ## Remove initial stuff
        box = wx.StaticBox(self.stat_panel, label=_("Statistical parameters"))
        sizerin = wx.StaticBoxSizer(box, wx.VERTICAL)
            
        checks = list(dclab.statistics.Statistics.available_methods.keys())
        checks.sort()

        for c in checks:
            # label id (b/c of sorting)
            cb = wx.CheckBox(self.stat_panel, label=c, name=c)
            sizerin.Add(cb)
            cb.SetValue(True)
        
        self.stat_panel.SetupScrolling()
        self.stat_panel.SetSizer(sizerin)
        sizerin.Fit(self.stat_panel)
