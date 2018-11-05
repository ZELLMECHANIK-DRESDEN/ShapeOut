#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - legend plot"""
from __future__ import division, unicode_literals

# Chaco imports
import chaco.api as ca
import chaco.tools.api as cta
import numpy as np


def legend_plot(measurements, title_font="modern 12",
                title="Legend", legend_font="modern 9"):
    """Plot legend for an RT-DC data set
    
    Parameters
    ----------
    measurements : list of RTDCBase
        Contains color information and titel.
        - mm.config["plotting"]["contour color"]
        - mm.title
    """
    # The legend is actually a list of plot labels
    aplot = ca.Plot()
    # normalize range from zero to 100 for convenience
    aplot.range2d.high=(100,100)
    aplot.range2d.low=(0,0)
    aplot.title = title
    aplot.title_font = title_font
    leftmarg = 7
    fname, fsize = legend_font.rsplit(" ", 1)
    fsize = int(fsize)
    autoscale = measurements[0].config["plotting"]["legend autoscaled"]
    if autoscale and len(measurements)>=10:
        # This case makes the legend entries fit into the plot window 
        lm = len(measurements)
        marker_size = int(np.floor(5/lm*9))
        fsize = int(np.floor(fsize/lm*9))
        increment = 100/(lm+1)
        # This is a heuristic setting that works for most plots:
        # (not sure how chaco defines marker positions)
        label_position = -6*(5/lm*9)**.3
    else:
        marker_size = 5
        increment = 10
        label_position = -10
    legend_font = " ".join([fname, str(fsize)])
    toppos = 100 - increment
        
    for mm in measurements:
        if mm.config["plotting"]["scatter title colored"]:
            mmlabelcolor = mm.config["plotting"]["contour color"]
        else:
            mmlabelcolor = "black"
        alabel = ca.DataLabel(
                        component=aplot, 
                        label_position=[0,label_position],
                        data_point=(leftmarg,toppos),
                        padding_bottom=0,
                        marker_size=marker_size,
                        bgcolor="transparent",
                        border_color="transparent",
                        label_text="  "+mm.title,
                        font=legend_font,
                        text_color=mmlabelcolor,
                        marker="circle",
                        marker_color="transparent",
                        marker_line_color=mm.config["plotting"]["contour color"],
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