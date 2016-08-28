#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - legend plot

"""
from __future__ import division, unicode_literals

# Chaco imports
import chaco.api as ca
import chaco.tools.api as cta


def legend_plot(measurements, title_font="modern 12",
                title="Legend", legend_font="modern 9"):
    """ Plot contour for two axes of an RTDC measurement
    
    Parameters
    ----------
    measurements : list of instances of RTDS_DataSet
        Contains color information and titel.
        - mm.Configuration["Plotting"]["Contour Color"]
        - mm.title
    """
    aplot = ca.Plot()
    # normalize our data in range zero to 100
    aplot.range2d.high=(100,100)
    aplot.range2d.low=(0,0)
    aplot.title = title
    aplot.title_font = title_font
    leftmarg = 7
    toppos = 90
    increment = 10
    for mm in measurements:
        if mm.Configuration["Plotting"]["Scatter Title Colored"]:
            mmlabelcolor = mm.Configuration["Plotting"]["Contour Color"]
        else:
            mmlabelcolor = "black"
        alabel = ca.DataLabel(
                        component=aplot, 
                        label_position=[0,-increment],
                        data_point=(leftmarg,toppos),
                        padding_bottom=0,
                        marker_size=5,
                        bgcolor="transparent",
                        border_color="transparent",
                        label_text="  "+mm.title,
                        font=legend_font,
                        text_color=mmlabelcolor,
                        marker="circle",
                        marker_color="transparent",
                        marker_line_color=mm.Configuration["Plotting"]["Contour Color"],
                        show_label_coords=False,
                        arrow_visible=False
                              )
        toppos -= increment
        aplot.overlays.append(alabel)
    
    aplot.padding_left = 0
    aplot.y_axis = None
    aplot.x_axis = None
    aplot.x_grid = None
    aplot.y_grid = None

    # pan tool
    pan = cta.PanTool(aplot, drag_button="left")
    aplot.tools.append(pan)

    return aplot