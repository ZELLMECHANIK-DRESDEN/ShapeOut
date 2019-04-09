#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - contour plot methods"""
from __future__ import division, unicode_literals

import time

import chaco.api as ca
import chaco.tools.api as cta
from dclab import definitions as dfn
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

    if mm.config["filtering"]["enable filters"]:
        x0 = mm[xax][mm._filter]
        y0 = mm[yax][mm._filter]
    else:
        # filtering disabled
        x0 = mm[xax]
        y0 = mm[yax]

    for ii, mm in enumerate(analysis):
        cname = "con_{}_{}".format(ii, mm.identifier)
        if cname in plot.plots:
            plot.delplot(cname)

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

        print("...KDE contour time {}: {:.2f}s".format(kde_type, time.time()-a))

        pd.set_data(cname, density)

        # contour widths
        if "contour width" in mm.config["plotting"]:
            cwidth = mm.config["plotting"]["contour width"]
        else:
            cwidth = 1.2

        levels = np.array([mm.config["plotting"]["contour level 1"],
                           mm.config["plotting"]["contour level 2"]])
        mode = mm.config["plotting"]["contour level mode"]
        if mode == "fraction":
            plev = list(np.nanmax(density) * levels)
        elif mode == "quantile":
            pdensity = mm.get_kde_scatter(xax=xax,
                                          yax=yax,
                                          xscale=scalex,
                                          yscale=scaley,
                                          kde_type=kde_type,
                                          kde_kwargs=kde_kwargs,
                                          )
            plev = list(np.nanpercentile(pdensity, q=levels*100))

        else:
            raise ValueError("Unknown contour level mode `{}`!".format(mode))

        if len(plev) == 2:
            styles = ["dot", "solid"]
            widths = [cwidth*.7, cwidth] # make outer lines slightly smaller
        else:
            styles = "solid"
            widths = cwidth

        cplot = plot.contour_plot(cname,
                          name=cname,
                          type="line",
                          xbounds=X,
                          ybounds=Y,
                          levels=plev,
                          colors=mm.config["plotting"]["contour color"],
                          styles=styles,
                          widths=widths,
                          index_scale=scalex,
                          value_scale=scaley,
                          )[0]
        # Workaround for plotting contour data on a log scale
        # (https://github.com/enthought/chaco/issues/300)
        # 2019-04-09: This does not resolve the problem. In case of a
        # logarithmic scale, there is an offset in the contour plotted.
        if scalex == "log":
            cplot.index_mapper._xmapper = ca.LogMapper(
                    range=cplot.index_range.x_range,
                    screen_bounds=cplot.index_mapper.screen_bounds[:2]
                    )
        if scaley == "log":
            cplot.index_mapper._ymapper = ca.LogMapper(
                    range=cplot.index_range.y_range,
                    screen_bounds=cplot.index_mapper.screen_bounds[:2]
                )
