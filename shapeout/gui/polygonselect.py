#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - polygon selection tool"""
from __future__ import division, print_function, unicode_literals

import chaco.tools.api as cta
import enable.api as ea
import numpy as np
import platform
import wx

from . import misc
from . import plot_scatter


class LineDrawer(cta.LineSegmentTool):
    """
    This class demonstrates how to customize the behavior of the
    LineSegmentTool via subclassing.
    
    Line segment drawing:
    - left click places a new point
    - moving over an existing point and left-dragging will reposition that point
    - moving over an existing point and ctrl-left-clicking will delete that point
    - pressing "Enter" will "finalize" the selection. This means that the
    tool's _finalize_selection() method will be called, and the list of
    drawn points will be reset. By default, _finalize_selection() does nothing,
    but subclasses can customize this.
    
    """
    def __init__(self, callback, axes, measurement, *args, **kwargs):
        cta.LineSegmentTool.__init__(self, *args, **kwargs)
        self.callback = callback
        self.axes = axes
        self.mm = measurement

    def _finalize_selection(self):
        # give Shape-Out the points
        results = {"points": self.points,
                   "axes": self.axes,
                   "measurement": self.mm,
                  }
        self.callback(results)



class LineDrawerWindow(wx.Frame):
    """
    Displays a window containing a line drawer
    """
    def __init__(self, parent, callback, *args, **kwargs):
        self.callback = callback
        self.parent = parent
        
        wx.Frame.__init__(self, parent, *args, **kwargs)
        self.SetMinSize((700,700))
        panel = wx.Panel(self)

        plot_window = ea.Window(panel)
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(plot_window.control, 1, wx.EXPAND, border=10)
        panel.SetSizer(vbox)
        vbox.Fit(panel)
        
        # status bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(1)

        text = wx.StaticText(self.statusbar, -1,
           label="'Click' to add points; press 'Enter' to add filter"+\
                 "; 'right click' to drag plot")
        rect = self.statusbar.GetFieldRect(0)
        posx = rect.x
        posy = rect.y
        #width = rect.width
        #height = rect.height
        if platform.system()=="Linux":
            posy += self.statusbar.GetBorderY()
        text.SetPosition((posx+5, posy))
        
        self.plot_window = plot_window
        self.panel = panel
        self.Centre()
        # Set window icon
        try:

            self.MainIcon = misc.getMainIcon()
            wx.Frame.SetIcon(self, self.MainIcon)
        except:
            self.MainIcon = None
        self.Show(True)

    def show_scatter(self, measurement, xax="area_um", yax="deform"):
        self.mm = measurement
        aplot = self._create_plot_component(measurement, xax=xax, yax=yax)
        aplot.padding = 50
        aplot.padding_left= 100
        self.plot_window.bgcolor = "white"
        self.plot_window.component = aplot
        self.plot_window.redraw()
        
        # Index all events and allow to hover above them to see the images
        self.event_indices = []
        my_plot = aplot.plots["scatter_events"][0]
        # Set up the trait handler for the selection
        id_ds = my_plot.index

        id_ds.on_trait_change(self.on_mouse_scatter,
                              "metadata_changed")
        self.event_indices.append(id_ds)
        self.myplot = aplot


    def _create_plot_component(self, measurement, xax, yax):
        # Create some data
        plot = plot_scatter.scatter_plot(measurement, panzoom=False)
        # Create a plot data obect and give it this data
        # Tweak some of the plot properties
        plot.title = "Click to add points, press Enter to add filter"
        plot.padding = 50
        plot.line_width = 1
        # Attach some tools to the plot
        pan = cta.PanTool(plot, drag_button="right", constrain_key="shift")
        plot.tools.append(pan)
        zoom = cta.ZoomTool(component=plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)
        plot.overlays.append(LineDrawer(self.callback, (xax, yax), measurement, plot))
        return plot


    def on_mouse_scatter(self):
        """
        Display an image of the event whenever the mouse hovers above an event.
        
        This method is a slightly simpler implementation of
        ``plot.MainPlotArea.OnMouseScatter``
        """
        thishov = None
        for id_ds in self.event_indices:
            hov = id_ds.metadata.get("hover", [])
            # Get hover data
            if len(hov) > 0:
                thishov = hov[0]

        if thishov is not None:
            # Get the cell and plot it
            dataset = self.mm
            # these are all cells that were plotted
            plotfilterid = np.where(dataset._plot_filter)[0]
            # this is the plot selection
            plot_sel = plotfilterid[thishov]
            # these are all the filtered cells
            filterid = np.where(dataset._filter)[0]
            actual_sel = filterid[plot_sel]
            
            mm_id = self.parent.frame.ImageArea.analysis.measurements.index(dataset)
            self.parent.frame.ImageArea.ShowEvent(mm_id=mm_id, evt_id=actual_sel)
