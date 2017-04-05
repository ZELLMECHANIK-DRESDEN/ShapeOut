#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - classes and methods for batch processing

"""
from __future__ import division, print_function, unicode_literals

import codecs
import numpy as np
import os
import wx
from wx.lib.scrolledpanel import ScrolledPanel

import dclab
from .. import analysis
from .. import tlabwrap



class BatchFilterFolder(wx.Frame):
    def __init__(self, parent, analysis):
        self.parent = parent
        self.analysis = analysis
        self.out_tsv_file = None
        self.tdms_files = None
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
            label=_("Apply the filter setting of one measurement\n"+\
                    "to all measurements within a folder and\n"+\
                    "save selected statistical parameters."))
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
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectMeasurement, self.dropdown)
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
                            label=_("Folder containing RT-DC measurements"))
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

        ## Output selection
        boxtsv = wx.StaticBox(panel, label=_("Output file"))
        tsvSizer = wx.StaticBoxSizer(boxtsv, wx.VERTICAL)
        btnbrwstsv = wx.Button(panel, wx.ID_ANY, _("Browse"))
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBrowseTSV, btnbrwstsv)
        self.WXtsv_text1 = wx.StaticText(panel,
                               label=_("Results of statistical analysis"))
        tsv2sizer = wx.BoxSizer(wx.HORIZONTAL)
        tsv2sizer.Add(btnbrwstsv)
        tsv2sizer.Add(self.WXtsv_text1, 0,
                      wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        tsvSizer.AddSpacer(5)
        tsvSizer.Add(tsv2sizer, 0,
                     wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.topSizer.Add(tsvSizer, 0, wx.EXPAND)

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
        wx.BeginBusyCursor()
        # Get selected axes
        axes = []
        for ch in self.axes_panel.GetChildren():
            if (isinstance(ch, wx._controls.CheckBox) and 
                ch.IsChecked()):
                name = ch.GetName()
                if name in dclab.dfn.uid:
                    axes.append(name)
        # Get selected columns
        col_dict = dclab.statistics.Statistics.available_methods
        columns = []
        for ch in self.stat_panel.GetChildren():
            if (isinstance(ch, wx._controls.CheckBox) and 
                ch.IsChecked()):
                name = ch.GetName()
                if name in col_dict:
                    columns.append(name)
        
        # Get filter configuration of selected measurement
        if self.rbtnhere.GetValue():
            mhere = self.analysis.measurements[self.dropdown.GetSelection()] 
            f_config = mhere.config

        # Compute statistics
        head = None
        rows = []
        
        # Process each tdms file separately to reduce memory usage
        for tdms in self.tdms_files:
            # Make analysis from tdms file
            anal = analysis.Analysis([tdms])
            # Apply configuration
            anal.SetParameters(f_config)
            mm = anal.measurements[0]
            # Apply filters
            mm.ApplyFilter()
            # Get statistics
            h, v = dclab.statistics.get_statistics(rtdc_ds=mm,
                                                   columns=columns,
                                                   axes=axes)
            if head is None:
                head = h
            else:
                assert h==head, "Problem with available columns/axes!"
            
            rows.append([mm.tdms_filename, mm.title]+v)

        head = ["TDMS file", "Title"] + head
        
        with codecs.open(self.out_tsv_file, "w", encoding="utf-8") as fd:
            header = u"\t".join([ h for h in head ])
            fd.write("# "+header+"\n")
        
        with open(self.out_tsv_file, "ab") as fd:
            for row in rows:
                fmt=["{:s}"]*2+["{:.10e}"]*len(v)
                line="\t".join(fmt).format(*row)
                fd.write(line+"\n")
        wx.EndBusyCursor()


    def OnBrowse(self, e=None):
        """ Let the user select a directory and search that directory
        for RT-DC data sets.
        """
        # make directory dialog
        dlg2 = wx.DirDialog(self,
                message=_("Please select directory containing measurements"),
                defaultPath=self.parent.config.get_dir("BatchFD"),
                style=wx.DD_DEFAULT_STYLE)
        
        if dlg2.ShowModal() == wx.ID_OK:
            thepath = dlg2.GetPath()
        else:
            thepath = None
        dlg2.Destroy()
        wx.Yield()
        if thepath is not None:
            wx.BeginBusyCursor()
            self.WXfold_text1.SetLabel(thepath)
            self.parent.config.set_dir(thepath, "BatchFD")
            # Search directory
            tree, _cols = tlabwrap.GetTDMSTreeGUI(thepath)
            self.WXfold_text2.SetLabel(_("Found {} measurement(s).").
                                       format(len(tree)))
            self.tdms_files = [ t[1][1] for t in tree]
            
            if self.out_tsv_file is not None:
                self.btnbatch.Enable()
            wx.EndBusyCursor()
        


    def OnBrowseTSV(self, e=None):
        dlg2 = wx.FileDialog(self,
                message=_("Please select an output file."),
                defaultDir=self.parent.config.get_dir("BatchOut"),
                style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
                wildcard=_("TSV files")+" (*.tsv)|*.tsv")
        
        if dlg2.ShowModal() == wx.ID_OK:
            thepath = dlg2.GetPath()
            if not thepath.endswith(".tsv"):
                thepath+=".tsv"
            self.WXtsv_text1.SetLabel(thepath)
            thedir = os.path.dirname(thepath)
            self.parent.config.set_dir(thedir, "BatchOut")
            self.out_tsv_file = thepath
        
        if self.tdms_files is not None:
            self.btnbatch.Enable()

    
    def OnRadioHere(self, e=None):
        meas = [ mm.title for mm in self.analysis.measurements ]
        self.dropdown.SetItems(meas)
        self.dropdown.SetSelection(0)
        self.OnSelectMeasurement()
        

    def OnRadioThere(self, e=None):
        print("there")
        self.OnUpdateAxes()
        self.filter_config = None
        
    
    def OnSelectMeasurement(self, e=None):
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
            for c in dclab.dfn.rdv:
                if np.sum(np.abs(getattr(mm, c))):
                    checks.append(dclab.dfn.cfgmap[c])
        else:
            for c in dclab.dfn.rdv:
                checks.append(dclab.dfn.cfgmap[c])

        checks = list(set(checks))
        labels = [ dclab.dfn.axlabels[c] for c in checks ]

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
