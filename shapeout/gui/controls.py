#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - control panels"""
from __future__ import division, print_function, unicode_literals

import numpy as np

import wx
from wx.lib.scrolledpanel import ScrolledPanel

import dclab
from dclab.rtdc_dataset import config as rt_config

from . import confparms
from . import plot_contour
from . import plot_scatter

from .controls_analyze import SubPanelAnalyze
from .controls_calculate import SubPanelCalculate
from .controls_contourplot import SubPanelPlotContour
from .controls_filter import SubPanelFilter
from .controls_info import SubPanelInfo
from .controls_plotting import SubPanelPlotting
from .controls_scatterplot import SubPanelPlotScatter
from .controls_statistics import SubPanelStatistics


class ControlPanel(ScrolledPanel):
    """"""
    def __init__(self, parent, frame):
        """Constructor"""
        ScrolledPanel.__init__(self, parent)
        self.SetupScrolling(scroll_y=True)
        self.SetupScrolling(scroll_x=True)
        
        self.frame = frame
        self.config = frame.config
        self.notebook = wx.Notebook(self)

        self.subpanels = []
        self.AddSubpanels()
        self.notebook.SetSelection(5)

        # Shortucut SHIFT+ENTER replots everything
        randomId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnChange, id=randomId)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT, wx.WXK_RETURN, randomId )])
        self.SetAcceleratorTable(accel_tbl)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)


    def AddSubpanels(self):
        notebook=self.notebook
        page_info = SubPanelInfo(notebook)
        notebook.AddPage(page_info, "Information")
        self.subpanels.append(page_info)
        self.page_info = page_info

        self.page_filter = SubPanelCalculate(notebook, funcparent=self)
        notebook.AddPage(self.page_filter, "Calculate")
        self.subpanels.append(self.page_filter)
        
        self.page_filter = SubPanelFilter(notebook, funcparent=self)
        notebook.AddPage(self.page_filter, "Filter")
        self.subpanels.append(self.page_filter)
        
        self.page_stat = SubPanelStatistics(notebook)
        notebook.AddPage(self.page_stat, "Statistics")
        self.subpanels.append(self.page_stat)
        
        self.page_cont = SubPanelAnalyze(notebook, funcparent=self)
        notebook.AddPage(self.page_cont, "Analyze")
        self.subpanels.append(self.page_cont)

        self.page_plot = SubPanelPlotting(notebook, funcparent=self)
        notebook.AddPage(self.page_plot, "Plotting")
        self.subpanels.append(self.page_plot)
        
        self.page_scat = SubPanelPlotScatter(notebook, funcparent=self)
        notebook.AddPage(self.page_scat, "Scatter Plot")
        self.subpanels.append(self.page_scat)

        self.page_cont = SubPanelPlotContour(notebook, funcparent=self)
        notebook.AddPage(self.page_cont, "Contour Plot")
        self.subpanels.append(self.page_cont)


    def NewAnalysis(self, anal=None):
        # destroy everything on Info panel and replot.
        if anal is not None:
            self.analysis = anal
        self.UpdatePages()
        self.OnChange()


    def OnChange(self, e=None):
        self.OnChangeFilter(updp=False, draw=False)
        self.OnChangePlot(updp=False)
        self.UpdatePages()


    def OnChangeFilter(self, e=None, updp=True, draw=True):
        # get all values
        wx.BeginBusyCursor()
        ctrls = self.page_filter.GetChildren()
        samdict = self.analysis.measurements[0].config.copy()["filtering"]
        newfilt = rt_config.CaseInsensitiveDict()

        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            name = c.GetName()
            if name in samdict:
                # box filters
                if isinstance(c, wx._controls.CheckBox):
                    newfilt[name] = bool(c.GetValue())
                else:
                    newfilt[name] = float(c.GetValue())

        chlist = self.page_filter.GetPolygonHtreeChecked()
        checked = []
        for ch in chlist:
            checked.append(ch.GetData())
        
        # Polygon filters are handled separately for each measurement.
        # This is done by the autobinding methods of the SubPanelFilter
        # - OnPolygonCombobox        (display filter for each mm)
        # - OnPolygonHtreeChecked    (change filter for each mm)
        #newfilt["Polygon Filters"] = checked
        
        cfg = { "filtering" : newfilt }
        
        # Apply base data limits
        if cfg["filtering"]["limit events auto"]:
            minsize = self.analysis.ForceSameDataSize()
            cfg["filtering"]["limit events"] = minsize
            for c in ctrls:
                name = c.GetName()
                if name == "limit events":
                    c.SetValue(str(minsize))
        self.analysis.SetParameters(cfg)

        if draw:
            # Only update the plotting data.
            # (Until version 0.6.1 the plots were recreated after
            #  each update, which caused a memory leak)
            plot_window = self.frame.PlotArea.mainplot.plot_window
            plots = plot_window.component.components
            for plot in plots:
                for mm in self.analysis.measurements:
                    if plot.id == mm.identifier:
                        plot_scatter.set_scatter_data(plot, mm)
                        plot_scatter.reset_inspector(plot)
    
                if plot.id == "ShapeOut_contour_plot":
                    plot_contour.set_contour_data(plot, self.analysis.measurements)
        
        if updp:
            self.UpdatePages()
        wx.EndBusyCursor()


    def OnChangePlot(self, e=None, updp=True):
        # Set plot order
        if hasattr(self.analysis, "measurements"):
            mms = [ self.analysis.measurements[ii] for ii in self.page_plot.plot_order ]
            # make sure that we don't miss any new measurements on the way.
            newmeas = len(self.analysis.measurements) - len(mms)
            if newmeas > 0:
                mms += self.analysis.measurements[-newmeas:]
            self.analysis.measurements = mms
        
        wx.BeginBusyCursor()
        
        ctrls = list(self.page_plot.GetChildren())
        ctrls += list(self.page_cont.GetChildren())
        ctrls += list(self.page_scat.GetChildren())
        samdict = self.analysis.measurements[0].config.copy()["plotting"]
        newfilt = rt_config.CaseInsensitiveDict()

        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            name = c.GetName()
            if name in samdict:
                var = name
                if isinstance(c, wx.ComboBox) and hasattr(c, "data"):
                    # handle combobox selections such that the string in the
                    # combobox does not matter, only the selection id.
                    cid = c.GetSelection()
                    if cid != -1:
                        val = c.data[cid]
                    else:
                        val = c.GetValue()
                else:
                    val = c.GetValue()

                var, val = rt_config.keyval_str2typ(var, val)
                newfilt[var] = val
            elif name.startswith("title "):
                # Change title of measurement
                for mm in self.analysis.measurements:
                    if mm.identifier == name[len("title "):]:
                        mm.title = c.GetValue()
            elif name.startswith("color "):
                # Change plotting color of measurement
                for mm in self.analysis.measurements:
                    if mm.identifier == name[len("title "):]:
                        col = c.GetColour()
                        col = np.array([col.Red(), col.Green(),
                                       col.Blue(), col.Alpha()])/255
                        mm.config["plotting"]["contour color"] = col.tolist()
        
        cfg = {"plotting": newfilt }

        self.analysis.SetParameters(cfg)

        # Update Plots
        self.frame.PlotArea.Plot(self.analysis)

        if updp:
            self.UpdatePages()
        wx.EndBusyCursor()


    def OnPolygonFilter(self, result):
        """ Called by polygon Window """
        pf = dclab.PolygonFilter(points=result["points"],
                                 axes=result["axes"])
        uid = pf.unique_id
        mcur = result["measurement"]
        # update list of polygon filters
        self.UpdatePages()
        # Determine the number of existing polygon filters
        npol = len(dclab.PolygonFilter.instances)

        if npol == 1 and mcur.format != "hierarchy":
            # apply to all measurements except hierarchy children
            for mm in self.analysis.measurements:
                if not mm.format == "hierarchy":
                    mm.config["filtering"]["polygon filters"].append(uid)
        else:
            # apply only to this one data set
            mcur.config["filtering"]["polygon filters"].append(uid)
        self.OnChangeFilter()


    def Reset(self, key, subkeys=[]):
        newcfg = confparms.GetDefaultConfiguration(key)
        if len(subkeys) != 0:
            for k in list(newcfg.keys()):
                if not k in subkeys:
                    newcfg.pop(k)
        self.analysis.SetParameters({key : newcfg})
        if key == "Plotting" and "Contour Plot" in subkeys:
            self.analysis.init_plot_accuracies()
        self.UpdatePages()
        self.frame.PlotArea.Plot(self.analysis)
        

    def UpdatePages(self):
        """ fills pages """
        sel = self.notebook.GetSelection()

        # Update page content        
        for page in self.subpanels:
            page.UpdatePanel(self.analysis)
            # workaround to force redrawing of Page:
            page.Layout()
            page.UpdateScrolling()
            page.Refresh()
            page.Update()

        # select previously selected page
        self.notebook.SetSelection(sel)
        
        # call all kinds of update functions such that
        # scrollbars don't disappear on Windows
        self.notebook.Layout()
        self.notebook.Refresh()
        self.notebook.Update()
        
        self.Layout()
        