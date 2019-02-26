#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - classes and methods for batch processing"""
from __future__ import division, print_function, unicode_literals

import io
import os
import wx
from wx.lib.scrolledpanel import ScrolledPanel

import dclab
from .. import analysis
from .. import meta_tool



class BatchFilterFolder(wx.Frame):
    def __init__(self, parent, analysis):
        self.parent = parent
        self.analysis = analysis
        self.out_tsv_file = None
        self.data_files = None
        self.axes_panel_sizer = None
        # Features checks
        self.toggled_event_features = True
        # Statistical parameters checks
        self.toggled_stat_parms = False

        # Get the window positioning correctly
        wx.Frame.__init__(self, parent=self.parent,
                          title="Batch-mode statistical summary",
                          style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## panel
        panel = self.panel = wx.Panel(self)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        # init
        self.topSizer.Add(
            wx.StaticText(panel,
            label="Apply the filter setting of one measurement\n"+\
                  "to all measurements within a folder and\n"+\
                  "save selected statistical parameters.")
            )
        self.topSizer.AddSpacer(10)
        ## Filter source selection
        boxleft = wx.StaticBox(panel, label="Filter settings")
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
        self.topSizer.AddSpacer(10)

        ## Folder selection
        boxfold = wx.StaticBox(panel, label="Input folder")
        foldSizer = wx.StaticBoxSizer(boxfold, wx.VERTICAL)
        btnbrws = wx.Button(panel, wx.ID_ANY, "Browse")
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, btnbrws)
        self.WXfold_text1 = wx.StaticText(panel,
                            label="Folder containing RT-DC measurements")
        self.WXdropdown_flowrate = wx.ComboBox(panel, -1, "All measurements", (15, 30),
                                               wx.DefaultSize, ["All measurements"],
                                               wx.CB_DROPDOWN|wx.CB_READONLY)
        self.WXdropdown_flowrate.Disable()
        self.WXdropdown_region = wx.ComboBox(panel, -1, "Channel and Reservoir", (15, 30),
                                               wx.DefaultSize, ["Channel and Reservoir",
                                                                "Channel only",
                                                                "Reservoir only"],
                                               wx.CB_DROPDOWN|wx.CB_READONLY)
        fold2sizer = wx.BoxSizer(wx.HORIZONTAL)
        fold2sizer.Add(btnbrws)
        fold2sizer.Add(self.WXfold_text1, 0,
                       wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        foldSizer.AddSpacer(5)
        foldSizer.Add(fold2sizer, 0,
                      wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        foldSizer.Add(self.WXdropdown_flowrate, 0, wx.EXPAND|wx.ALL)
        foldSizer.Add(self.WXdropdown_region, 0, wx.EXPAND|wx.ALL)
        foldSizer.AddSpacer(5)
        self.topSizer.Add(foldSizer, 0, wx.EXPAND)
        self.topSizer.AddSpacer(10)

        ## Axes checkboxes
        self.axes_panel = ScrolledPanel(panel, -1, size=(-1,200))
        self.axes_panel.SetupScrolling()
        self.topSizer.Add(self.axes_panel, 1, wx.EXPAND)
        self.topSizer.AddSpacer(10)

        ## Statistical parameters
        self.stat_panel = ScrolledPanel(panel, -1, size=(-1,200))
        self.stat_panel.SetupScrolling()
        self.topSizer.Add(self.stat_panel, 1, wx.EXPAND)
        self.topSizer.AddSpacer(10)
        self.SetupStatisticalParameters()

        ## Output selection
        boxtsv = wx.StaticBox(panel, label="Output file")
        tsvSizer = wx.StaticBoxSizer(boxtsv, wx.VERTICAL)
        btnbrwstsv = wx.Button(panel, wx.ID_ANY, "Browse")
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBrowseTSV, btnbrwstsv)
        self.WXtsv_text1 = wx.StaticText(panel,
                               label="No file selected")
        tsv2sizer = wx.BoxSizer(wx.HORIZONTAL)
        tsv2sizer.Add(btnbrwstsv)
        tsv2sizer.Add(self.WXtsv_text1, 0,
                      wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        tsvSizer.AddSpacer(5)
        tsvSizer.Add(tsv2sizer, 0,
                     wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.topSizer.Add(tsvSizer, 0, wx.EXPAND)

        ## Batch button
        btnbatch = wx.Button(self.panel, wx.ID_ANY,
                             "Assemble statistical summary")
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBatch, btnbatch)
        self.topSizer.Add(btnbatch, 0, wx.EXPAND)
        btnbatch.Disable()
        self.btnbatch = btnbatch

        panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self.panel)
        minsize = self.topSizer.GetMinSizeTuple()
        # increase minimum width by 100
        self.SetMinSize((minsize[0] + 100, minsize[1]))

        self.OnRadioHere()
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)


    def OnBatch(self, e=None):
        wx.BeginBusyCursor()
        # Get selected axes
        features = []
        for ch in self.axes_panel.GetChildren():
            if (isinstance(ch, wx._controls.CheckBox) and 
                ch.IsChecked()):
                name = ch.GetName()
                if name in dclab.dfn.scalar_feature_names:
                    features.append(name)
        # Get selected features
        col_dict = dclab.statistics.Statistics.available_methods
        methods = []
        for ch in self.stat_panel.GetChildren():
            if (isinstance(ch, wx._controls.CheckBox) and 
                ch.IsChecked()):
                name = ch.GetName()
                if name in col_dict:
                    methods.append(name)
        # Get filter configuration of selected measurement
        if self.rbtnhere.GetValue():
            mhere = self.analysis.measurements[self.dropdown.GetSelection()] 
            f_config = mhere.config
        # Compute statistics
        head = None
        rows = []
        # Determine which flow rates to use
        idflow = self.WXdropdown_flowrate.GetSelection() - 1
        if idflow < 0:
            files = self.data_files
        else:
            files = self.flow_dict[self.flow_rates[idflow]] 
        # Filter regions
        regid = self.WXdropdown_region.GetSelection()
        if regid > 0:
            if regid == 1:
                reg = "channel"
            elif regid == 2:
                reg = "reservoir"
            newfiles = []
            for tt in files:
                if meta_tool.get_chip_region(tt) == reg:
                    newfiles.append(tt)
            files = newfiles
        if not files:
            raise ValueError("No valid measurements with current selection!")
        
        # Process each data file separately to reduce memory usage
        for data in files:
            # Make analysis from data file
            anal = analysis.Analysis([data], config=f_config)
            mm = anal.measurements[0]
            # Apply filters
            mm.apply_filter()
            # Get statistics
            h, v = dclab.statistics.get_statistics(ds=mm,
                                                   methods=methods,
                                                   features=features)
            if head is None:
                head = h
            else:
                assert h==head, "Problem with available methods/features!"
            
            rows.append([mm.path, mm.title]+v)

        head = ["data file", "Title"] + head
        
        with io.open(self.out_tsv_file, "w") as fd:
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
                message="Please select directory containing measurements",
                defaultPath=self.parent.config.get_path("BatchFD"),
                style=wx.DD_DEFAULT_STYLE)
        
        if dlg2.ShowModal() == wx.ID_OK:
            thepath = dlg2.GetPath().encode("utf-8")
        else:
            thepath = None
        dlg2.Destroy()
        wx.Yield()
        if thepath is not None:
            wx.BeginBusyCursor()
            self.WXfold_text1.SetLabel(thepath)
            self.parent.config.set_path(thepath, "BatchFD")
            # Search directory
            tree, _cols = meta_tool.collect_data_tree(thepath)
            self.data_files = [ t[1][1] for t in tree ]
            
            if self.out_tsv_file is not None:
                self.btnbatch.Enable()
            wx.EndBusyCursor()
        
        # Update WXdropdown_flowrate and self.flow_rates
        # Determine flow rates
        flow_dict = {}
        for tt in self.data_files:
            fr = meta_tool.get_flow_rate(tt)
            if fr not in flow_dict:
                flow_dict[fr] = []
            flow_dict[fr].append(tt)
        selections = ["All measurements ({})".format(len(self.data_files))]
        self.flow_rates = list(flow_dict.keys())
        self.flow_rates.sort()
        for fr in self.flow_rates:
            num = len(flow_dict[fr])
            selections += ["Flow rate {} µl/s ({})".format(fr, num)] 
        self.WXdropdown_flowrate.SetItems(selections)
        self.WXdropdown_flowrate.SetSelection(0)
        self.WXdropdown_flowrate.Enable()
        self.flow_dict = flow_dict


    def OnBrowseTSV(self, e=None):
        dlg2 = wx.FileDialog(self,
                message="Please select an output file.",
                defaultDir=self.parent.config.get_path("BatchOut"),
                style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
                wildcard="TSV files"+" (*.tsv)|*.tsv")
        
        if dlg2.ShowModal() == wx.ID_OK:
            thepath = dlg2.GetPath().encode("utf-8")
            if not thepath.endswith(".tsv"):
                thepath+=".tsv"
            self.WXtsv_text1.SetLabel(thepath)
            thedir = os.path.dirname(thepath)
            self.parent.config.set_path(thedir, "BatchOut")
            self.out_tsv_file = thepath
        
        if self.data_files is not None:
            self.btnbatch.Enable()

    
    def OnRadioHere(self, e=None):
        meas = [ mm.title for mm in self.analysis.measurements ]
        self.dropdown.SetItems(meas)
        self.dropdown.SetSelection(0)
        self.OnSelectMeasurement()
        

    def OnRadioThere(self, e=None):
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
            box = wx.StaticBox(self.axes_panel, label="Event features")
            sizerbox = wx.StaticBoxSizer(box, wx.HORIZONTAL)
            sizerin = wx.BoxSizer(orient=wx.VERTICAL)
            sizerbox.Add(sizerin)
            sizersel = wx.BoxSizer(orient=wx.VERTICAL)
            btnselect = wx.Button(self.axes_panel, wx.ID_ANY, "(De-)select all")
            sizersel.Add(btnselect, 0, wx.ALIGN_RIGHT)
            sizerbox.Add(sizersel, 1, wx.EXPAND|wx.ALIGN_RIGHT)
            self.Bind(wx.EVT_BUTTON, self.OnToggleAllEventFeatures, btnselect)
            sizerbox.AddSpacer(5)

        self.axes_panel_sizer = sizerin

        checks = []
        if self.rbtnhere.Value:
            sel = self.dropdown.GetSelection()
            mm = self.analysis.measurements[sel]
            for c in dclab.dfn.scalar_feature_names:
                if c in mm:
                    checks.append(c)
        else:
            for c in dclab.dfn.scalar_feature_names:
                checks.append(c)

        checks = list(set(checks))
        labels = [ dclab.dfn.feature_name2label[c] for c in checks ]

        # Sort checks according to labels
        checks = [x for (_y,x) in sorted(zip(labels,checks))]
        labels.sort()

        for c,l in zip(checks, labels):
            # label id (b/c of sorting)
            label = l
            cb = wx.CheckBox(self.axes_panel, label=label, name=c)
            sizerin.Add(cb)
            if c in self.analysis.GetPlotAxes():
                cb.SetValue(True)
        
        self.axes_panel.SetupScrolling()
        self.axes_panel.SetSizer(sizerbox)
        sizerbox.Fit(self.axes_panel)
        self.topSizer.Fit(self.panel)
        size=self.topSizer.GetMinSizeTuple()
        self.SetSize((size[0]+1, -1))
        self.SetSize((size[0]-1, -1))


    def OnToggleAllEventFeatures(self, e=None):
        """Set all values of the event features to 
        `self.toggled_event_features` and invert
        `self.toggled_event_features`.
        """
        panel = self.axes_panel
        for ch in panel.GetChildren():
            if isinstance(ch, wx._controls.CheckBox):
                ch.SetValue(self.toggled_event_features)
            
        # Invert for next execution
        self.toggled_event_features = not self.toggled_event_features


    def OnToggleAllStatParms(self, e=None):
        """Set all values of the statistical parameters to 
        `self.toggled_stat_parms` and invert
        `self.toggled_stat_parms`.
        """
        panel = self.stat_panel
        for ch in panel.GetChildren():
            if isinstance(ch, wx._controls.CheckBox):
                ch.SetValue(self.toggled_stat_parms)
            
        # Invert for next execution
        self.toggled_stat_parms = not self.toggled_stat_parms


    def SetupStatisticalParameters(self, e=None):
        ## Remove initial stuff
        box = wx.StaticBox(self.stat_panel, label="Statistical parameters")
        sizerbox = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        sizerin = wx.BoxSizer(orient=wx.VERTICAL)
        sizerbox.Add(sizerin)
        sizersel = wx.BoxSizer(orient=wx.VERTICAL)
        btnselect = wx.Button(self.stat_panel, wx.ID_ANY, "(De-)select all")
        sizersel.Add(btnselect, 0, wx.ALIGN_RIGHT)
        sizerbox.Add(sizersel, 1, wx.EXPAND|wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnToggleAllStatParms, btnselect)
        sizerbox.AddSpacer(5)
            
        checks = list(dclab.statistics.Statistics.available_methods.keys())
        checks.sort()

        for c in checks:
            # label id (b/c of sorting)
            cb = wx.CheckBox(self.stat_panel, label=c, name=c)
            sizerin.Add(cb)
            cb.SetValue(True)

        self.stat_panel.SetupScrolling()
        self.stat_panel.SetSizer(sizerbox)
        sizerbox.Fit(self.stat_panel)
