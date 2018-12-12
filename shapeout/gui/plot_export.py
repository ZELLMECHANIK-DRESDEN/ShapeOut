#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - plot export"""
from __future__ import division, print_function

import chaco
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from chaco.svg_graphics_context import SVGGraphicsContext
import chaco.api as ca
import os
import warnings
import wx

from kiva.fonttools import font_manager

# Override default font families, because 'Bitstream Vera Sans'
# is not always available.
font_manager.fontManager.defaultFamily = {
            'ttf': 'sans-serif',
            'afm': 'sans-serif'}


def export_plot_pdf(parent):
    dlg = wx.FileDialog(parent, "Export plot as PDF", 
                        parent.config.get_path("PDF"), "",
                        "PDF file"+" (*.pdf)|*.pdf",
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath().encode("utf-8")
        if not path.endswith(".pdf"):
            path += ".pdf"
        parent.config.set_path(os.path.dirname(path), "PDF")
        container = parent.PlotArea.mainplot.container

        retol = hide_scatter_inspector(container)
        
        #old_height = container.height
        #old_width = container.width
        
        
        
        #a4_factor = 297/210
        ## Segmentation-faults:
        #from chaco.api import PlotGraphicsContext
        #gc = PlotGraphicsContext((int(container.outer_width), int(container.outer_height)))
        #container.draw(gc, mode="normal")
        #gc.save(path)

        #container.auto_size=True
        #container.auto_center=True
        
        # get inner_boundary
        (bx, by) = container.outer_bounds
        
        #(x, y) = (bx, by) = container.outer_bounds
        #x2 = 0,
        #y2 = 0
        #for c in container.components:
        #    x = min(c.x, x)
        #    y = min(c.y, y)
        #    x2 = max(c.x2, x2)
        #    y2 = max(c.y2, y2)
        #container.set_outer_bounds(0, (x2-x))
        #container.set_outer_bounds(1, (y2-y))

        # Correction factor 0.9 wih size of plots yields
        # approximately the right size for all kinds of container
        # shapes.
        container.set_outer_bounds(0, (300)*container.shape[1]**.9)
        container.set_outer_bounds(1, (300)*container.shape[0]**.9)
        
        # scatter plot classes
        class_sp = (chaco.colormapped_scatterplot.ColormappedScatterPlot,
                    chaco.scatterplot.ScatterPlot)
        
        for c in container.components:
            for comp in c.components:
                if isinstance(comp, class_sp):
                    comp.marker_size /= 2
        
        dest_box = (.01, .01, -.01, -.01)
        try:
            gc = PdfPlotGraphicsContext(filename=path,
                                dest_box = dest_box,
                                pagesize="landscape_A4")
        except KeyError:
            warnings.warn("'landscape_A4' not defined for pdf "+\
                          "export. Please update `chaco`.")
            gc = PdfPlotGraphicsContext(filename=path,
                                dest_box = dest_box,
                                pagesize="A4")
        # draw the plot
        gc.render_component(container, halign="center",
                            valign="top")
        #Start a new page for subsequent draw commands.
        gc.save()
        container.set_outer_bounds(0, bx)
        container.set_outer_bounds(1, by)

        for c in container.components:
            for comp in c.components:
                if isinstance(comp, class_sp):
                    comp.marker_size *= 2

        if retol is not None:
            retol.visible = True


def export_plot_png(parent):
    # PNG export is not functional in chaco
    # https://github.com/enthought/chaco/issues/295
    dlg = wx.FileDialog(parent, "Export plot as PNG", 
                        parent.config.get_path("PNG"), "",
                        "PNG file (*.png)|*.png",
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath().encode("utf-8")
        if not path.endswith(".png"):
            path += ".png"
        parent.config.set_path(os.path.dirname(path), "PNG")
        container = parent.PlotArea.mainplot.container
        
        # get inner_boundary
        p = container

        dpi=600
        p.do_layout(force=True)
        gc = ca.PlotGraphicsContext(tuple(p.outer_bounds), dpi=dpi)

        # temporarily turn off the backbuffer for offscreen rendering
        use_backbuffer = p.use_backbuffer
        p.use_backbuffer = False
        p.draw(gc)
        #gc.render_component(p)

        gc.save(path)

        p.use_backbuffer = use_backbuffer
        

def export_plot_svg(parent):
    dlg = wx.FileDialog(parent, "Export plot as SVG", 
                        parent.config.get_path("SVG"), "",
                        "SVG file"+" (*.svg)|*.svg",
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath().encode("utf-8")
        if not path.endswith(".svg"):
            path += ".svg"
        parent.config.set_path(os.path.dirname(path), "SVG")
        container = parent.PlotArea.mainplot.container

        retol = hide_scatter_inspector(container)
       
        container.do_layout(force=True)
        plot = container.components[0]
        gc = SVGGraphicsContext(plot.outer_bounds)
        gc.render_component(plot.components[-1])
        #Start a new page for subsequent draw commands.
        gc.save(path)

        if retol is not None:
            retol.visible = True



def hide_scatter_inspector(container):
    retol = None
    for aplot in container.components:
        if "scatter_events" in aplot.plots:
            theplot = aplot.plots["scatter_events"][0]
            for ol in theplot.overlays:
                if isinstance(ol, ca.ScatterInspectorOverlay):
                    if ol.visible == True:
                        retol = ol
                    ol.visible = False
    return retol
