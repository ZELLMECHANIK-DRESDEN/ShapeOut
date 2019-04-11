#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - contour plot methods"""
from __future__ import division, unicode_literals

import time

import chaco.api as ca
import chaco.tools.api as cta
from dclab import definitions as dfn
from dclab import kde_contours
import numpy as np

from . import plot_common
from .. import analysis as ana


def contour_plot(analysis, axContour=None, wxtext=False, square=True):
    """Plot contour for two axes of an RT-DC measurement
    
    Parameters
    ----------
    measurement : RTDCBase
        Contains measurement data.
    axContour : instance of matplotlib `Axis`
        Plotting axis for the contour.
    square : bool
        The plot has square shape.
    """
    mm = analysis[0]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()

    # Commence plotting
    if axContour is not None:
        raise NotImplementedError("Tell Chaco to reuse plots?")

    pd = ca.ArrayPlotData()
    contour_plot = ca.Plot(pd)
    contour_plot.id = "ShapeOut_contour_plot"

    scalex = mm.config["plotting"]["scale x"].lower()
    scaley = mm.config["plotting"]["scale y"].lower()

    contour_plot.index_scale = scalex
    contour_plot.value_scale = scaley

    # Add isoelastics only if all measurements have the same channel width
    try:
        analysis.get_config_value("setup", "channel width")
    except ana.MultipleValuesError:
        pass
    else:
        isoel = plot_common.get_isoelastics(mm)
        if isoel:
            for ii, data in enumerate(isoel):
                x_key = 'isoel_x'+str(ii)
                y_key = 'isoel_y'+str(ii)
                pd.set_data(x_key, data[:,0])
                pd.set_data(y_key, data[:,1])
                contour_plot.plot((x_key, y_key),
                                  color="gray",
                                  index_scale=scalex,
                                  value_scale=scaley)
    #colors = [ "".join(map(chr, np.array(c[:3]*255,dtype=int))).encode('hex') for c in colors ]

    set_contour_data(contour_plot, analysis)

    # Axes
    left_axis = ca.PlotAxis(contour_plot, orientation='left',
                            title=dfn.feature_name2label[yax],
                            tick_generator=plot_common.MyTickGenerator())
    
    bottom_axis = ca.PlotAxis(contour_plot, orientation='bottom',
                              title=dfn.feature_name2label[xax],
                              tick_generator=plot_common.MyTickGenerator())
    # Show log scale only with 10** values (#56)
    contour_plot.index_axis.tick_generator=plot_common.MyTickGenerator()
    contour_plot.value_axis.tick_generator=plot_common.MyTickGenerator()
    contour_plot.overlays.append(left_axis)
    contour_plot.overlays.append(bottom_axis)

    contour_plot.title = "Contours"

    contour_plot.title_font = "modern 12"

    # zoom tool
    zoom = cta.ZoomTool(contour_plot,
                        tool_mode="box",
                        color="beige",
                        minimum_screen_delta=50,
                        border_color="black",
                        border_size=1,
                        always_on=True,
                        drag_button="right",
                        enable_wheel=True,
                        zoom_factor=1.1)
    contour_plot.tools.append(zoom)
    contour_plot.aspect_ratio = 1
    contour_plot.use_downsampling = True
    
    # pan tool
    pan = cta.PanTool(contour_plot, drag_button="left")

    contour_plot.tools.append(pan)

    return contour_plot


def set_contour_data(plot, analysis):
    pd = plot.data
    # Plotting area
    mm = analysis[0]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()

    scalex = mm.config["plotting"]["scale x"].lower()
    scaley = mm.config["plotting"]["scale y"].lower()

    plot.index_scale = scalex
    plot.value_scale = scaley

    for ii, mm in enumerate(analysis):

        x0 = mm[xax][mm.filter.all]
        y0 = mm[yax][mm.filter.all]

        # Check if there is data to compute a contour from
        if len(mm._filter)==0 or np.sum(mm._filter)==0:
            break

        kde_type = mm.config["plotting"]["kde"].lower()
        kde_kwargs = plot_common.get_kde_kwargs(
            x=x0,
            y=y0,
            kde_type=kde_type,
            xacc=mm.config["plotting"]["kde accuracy "+xax],
            yacc=mm.config["plotting"]["kde accuracy "+yax])
        # Accuracy for plotting contour data
        xacc = mm.config["plotting"]["contour accuracy "+xax]
        yacc = mm.config["plotting"]["contour accuracy "+yax]

        a = time.time()
        X, Y, density = mm.get_kde_contour(xax=xax,
                                           yax=yax,
                                           xacc=xacc,
                                           yacc=yacc,
                                           xscale=scalex,
                                           yscale=scaley,
                                           kde_type=kde_type,
                                           kde_kwargs=kde_kwargs,
                                           )

        if X.shape[0] == 1 or X.shape[1] == 1:
            raise ValueError("Please decrease value for contour accuracy!")

        print("...KDE contour time {}: {:.2f}s".format(kde_type, time.time()-a))

        # contour widths
        if "contour width" in mm.config["plotting"]:
            cwidth = mm.config["plotting"]["contour width"]
        else:
            cwidth = 1.2

        levels = np.array([mm.config["plotting"]["contour level 1"],
                           mm.config["plotting"]["contour level 2"]])
        mode = mm.config["plotting"]["contour level mode"]
        if mode == "fraction":
            plev = levels
        elif mode == "quantile":
            plev = kde_contours.get_quantile_levels(density,
                                                    x=X,
                                                    y=Y,
                                                    xp=x0,
                                                    yp=y0,
                                                    q=levels,
                                                    normalize=True)
        else:
            raise ValueError("Unknown contour level mode `{}`!".format(mode))

        styles = ["dot", "solid"]
        widths = [cwidth*.7, cwidth] # make outer lines slightly smaller

        contours = []
        for level in plev:
            cc = kde_contours.find_contours_level(density, x=X, y=Y, level=level)
            contours.append(cc)

        for ii, cc in enumerate(contours):
            for jj, cci in enumerate(cc):
                x_key = "contour_x_{}_{}_{}".format(mm.identifier, ii, jj)
                y_key = "contour_y_{}_{}_{}".format(mm.identifier, ii, jj)
                pd.set_data(x_key, cci[:,0])
                pd.set_data(y_key, cci[:,1])
                plot.plot((x_key, y_key),
                           line_style=styles[ii],
                           line_width=widths[ii],
                           color=mm.config["plotting"]["contour color"],
                           index_scale=scalex,
                           value_scale=scaley,
                           )
