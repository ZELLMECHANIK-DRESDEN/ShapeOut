#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - wx and chaco plot components"""
from __future__ import division, print_function, unicode_literals

import chaco.api as ca
import enable.api as ea

import numpy as np
import platform
import wx
import wx.lib.agw.flatnotebook as fnb

from . import plot_scatter
from . import plot_contour
from . import plot_legend

class PlotNotebook(fnb.FlatNotebook):
    """
    Flatnotebook class
    """
    def __init__(self, parent):
        """Constructor"""
        style = fnb.FNB_RIBBON_TABS|\
                fnb.FNB_TABS_BORDER_SIMPLE|fnb.FNB_NO_X_BUTTON|\
                fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NODRAG
        # Bugfix for Mac
        if platform.system().lower() in ["windows", "linux"]:
            style = style|fnb.FNB_HIDE_ON_SINGLE_TAB
        self.fnb = fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY,
                                             agwStyle=style)


class PlotPanel(wx.Panel):
    """"""
    def __init__(self, parent, frame):
        """Constructor"""
        wx.Panel.__init__(self, parent)
        
        self.frame = frame
        self.config = frame.config
        self.notebook = PlotNotebook(self) 

        self.mainplot = MainPlotArea(self.notebook, frame)
        self.AddPanel(self.mainplot, "Main Plot")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
    
    def AddPanel(self, panel, name):
        self.notebook.AddPage(panel, name)

    def Plot(self, anal=None):
        """
        convenience function that calls MainPlotArea.Plot
        """
        self.mainplot.Plot(anal)


class MainPlotArea(wx.Panel):
    def __init__(self, parent, frame):
        self.frame = frame
        wx.Panel.__init__(self, parent, -1)

        self.plot_window = ea.Window(self)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.plot_window.control, 1, wx.EXPAND)
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
        self.container = None
        self.scatter2measure = {}

    def Plot(self, anal=None):
        self._lastplot = -1
        self._lastselect = -1
        self._lasthover = -1
        
        if anal is None:
            anal = self.analysis
        
        self.analysis = anal

        # Determine the min/max plotting range
        xax, yax = self.analysis.GetPlotAxes()
        xscale = self.analysis.get_config_value("plotting", "scale x")
        yscale = self.analysis.get_config_value("plotting", "scale y")
        xmin, xmax = self.analysis.get_feat_range(feature=xax, scale=xscale)
        ymin, ymax = self.analysis.get_feat_range(feature=yax, scale=yscale)

        rows, cols, lcc, lll = anal.GetPlotGeometry()
        
        numplots = rows * cols

        if self.container is None:
            container = ca.GridPlotContainer(
                                  shape = (rows, cols),
                                  spacing = (0,0),
                                  padding = (0,0,0,0),
                                  valign = 'top',
                                  bgcolor = 'white',
                                  fill_padding = True,
                                  use_backbuffer = True)
            self.plot_window.component = container
        else:
            container = self.container
            for pl in list(container.components):
                # Reset the handler for changing the plotting range
                # to avoid accidentally resetting when deleting the plots.
                pl.range2d.on_trait_change(self.OnPlotRangeChanged, remove=True)
                # Delete all plots
                for sp in list(pl.plots.keys()):
                    pl.delplot(sp)
                container.remove(pl)
                del pl
            container.shape = (rows, cols)
            # Call this method as a workaround for ValueError in
            # plot_containers.py line 615.
            container.get_preferred_size()
        
        maxplots = min(len(anal.measurements), numplots)
        
        self.index_datasources = []

        # dictionary mapping plot objects to data for scatter plots
        scatter2measure = {}

        c_plot = 0
        legend_plotted = False
        range_joined = []
        for j in range(rows):
            for i in range(cols):
                #k = i + j*rows
                if (i == cols-1 and j == 0 and lcc == 1):
                    # Contour plot in upper right corner
                    aplot = plot_contour.contour_plot(anal)
                    range_joined.append(aplot)
                elif (i == cols-1 and j == 1 and lll == 1):
                    # Legend plot below contour plot
                    aplot = plot_legend.legend_plot(anal.measurements)
                    legend_plotted = True
                elif c_plot < maxplots:
                    # Scatter Plot
                    aplot = plot_scatter.scatter_plot(anal.measurements[c_plot])
                    scatter2measure[aplot] = anal.measurements[c_plot]
                    range_joined.append(aplot)
                    c_plot += 1
                    # Retrieve the plot hooked to selection tool
                    my_plot = aplot.plots["scatter_events"][0]
                    # Set up the trait handler for the selection
                    id_ds = my_plot.index

                    id_ds.on_trait_change(self.OnMouseScatter,
                                          "metadata_changed")
                    self.index_datasources.append((aplot, id_ds))
                    # Set plotting range
                    aplot.index_mapper.range.low = xmin
                    aplot.index_mapper.range.high = xmax
                    aplot.value_mapper.range.low = ymin
                    aplot.value_mapper.range.high = ymax
                elif (not legend_plotted and lll == 1 and rows == 1) :
                    # Legend plot in next free window
                    aplot = plot_legend.legend_plot(anal.measurements)
                    legend_plotted = True
                else:
                    # dummy plot
                    aplot = ca.Plot()
                    aplot.aspect_ratio = 1
                    aplot.range2d.low = (0,0)
                    aplot.range2d.high = (1,1)
                    aplot.y_axis = None
                    aplot.x_axis = None
                    aplot.x_grid = None
                    aplot.y_grid = None
                
                container.add(aplot)

        # connect all plots' panning and zooming
        for comp in range_joined[1:]:
            comp.range2d = range_joined[0].range2d

        # Connect range with displayed range
        if len(range_joined):
            range_joined[0].range2d.on_trait_change(self.OnPlotRangeChanged)

        container.padding = 10
        container.padding_left = 30
        container.padding_right = 5

        (bx, by) = container.outer_bounds
        container.set_outer_bounds(0, bx)
        container.set_outer_bounds(1, by)
        self.container = container
        del self.scatter2measure
        self.scatter2measure = scatter2measure

        self.plot_window.redraw()
        # Update the image plot (dropdown choices, etc.)
        self.frame.ImageArea.UpdateAnalysis(anal)


    def OnPlotRangeChanged(self, obj, name, new):
        """ Is called by traits on_trait_change for plots
            
        Updates the data in panel top
        """
        ctrls = self.frame.PanelTop.page_plot.GetChildren()
        newfilt = {}
        xax, yax = self.analysis.GetPlotAxes()
 
        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            name = c.GetName()
            if name == xax+" min":
                ol0 = float("{:.4e}".format(obj.low[0]))
                newfilt[name] = ol0
                c.SetValue(unicode(ol0))
            elif name == xax+" max":
                oh0 = float("{:.4e}".format(obj.high[0]))
                newfilt[name] = oh0
                c.SetValue(unicode(oh0))
            elif name == yax+" min":
                ol1 = float("{:.4e}".format(obj.low[1]))
                newfilt[name] =ol1
                c.SetValue(unicode(ol1))
            elif name == yax+" max":
                oh1 = float("{:.4e}".format(obj.high[1]))
                newfilt[name] = oh1
                c.SetValue(unicode(oh1))

        cfg = {"plotting" : newfilt}
        self.analysis.SetParameters(cfg)


    def OnMouseScatter(self):
        # TODO:
        # - detect when hover is stuck
        # - display additional information in plot
        
        if not hasattr(self, "_lasthover"):
            self._lasthover = False
        if not hasattr(self, "_lastselect"):
            self._lastselect = False
        if not hasattr(self, "_lastplothover"):
            self._lastplothover = False
        if not hasattr(self, "_lastplotselect"):
            self._lastplotselect = False
        
        thisplothover = None
        thisplotselect = None
        thissel = None
        thishov = None
        for (aplot, id_ds) in self.index_datasources:
            hov = id_ds.metadata.get("hover", [])
            sel = id_ds.metadata.get("selections", [])
            # Get hover data
            if len(hov) > 0:
                thisplothover = aplot
                thishov = hov[0]
                # Get select data
                if len(sel) != 0:
                    thisplotselect = aplot
                    thissel = sel[0]
        
        if thishov is None:        
            for (aplot, id_ds) in self.index_datasources:
                if self._lastplothover is aplot:
                    thisplothover = aplot

        for (aplot, id_ds) in self.index_datasources:
            my_plot = aplot.plots["scatter_events"][0]
            # Show or hide overlays:
            if thisplothover is aplot:
                my_plot.overlays[0].visible = True
            else:
                my_plot.overlays[0].visible = False

        action = False

        if thisplotselect is not None:
            if self._lastplotselect is thisplotselect:
                # We are in the same plot
                if self._lastselect != thissel:
                    # We have a different cell
                    action = True
            else:
                # We have a new plot
                action = True

        if action:
            # Get the cell and plot it
            mm = self.scatter2measure[thisplotselect]
            # Update the currently plotted list of events `mm._plot_filter`
            xax = mm.config["plotting"]["axis x"].lower()
            yax = mm.config["plotting"]["axis y"].lower()
            plotdic = mm.config.copy()["plotting"]
            downsample = plotdic["downsampling"]*plotdic["downsample events"]
            mm.get_downsampled_scatter(xax=xax, yax=yax, downsample=downsample)
            # these are all cells that were plotted
            # (not neccessarily *all* cells that were filtered away)
            plotfilterid = np.where(mm._plot_filter)[0]
            # these are all the filtered cells
            filterid = np.where(mm._filter)[0]
            
            # this is the plot selection
            plot_sel = plotfilterid[thissel]
            actual_sel = filterid[plot_sel]
            
            mm_id = self.analysis.measurements.index(mm)
            self.frame.ImageArea.ShowEvent(mm_id=mm_id, evt_id=actual_sel)

        if not thisplothover is None:
            self._lastplothover = thisplothover
        if not thisplotselect is None:
            self._lastplotselect = thisplotselect
        self._lasthover = thishov
        self._lastselect = thissel
