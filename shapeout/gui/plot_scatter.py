#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - scatter plot methods

"""
from __future__ import division, unicode_literals

import chaco.api as ca
import chaco.tools.api as cta
from dclab import definitions as dfn
import numpy as np
import time
import warnings

from ..tlabwrap import isoelastics
from . import plot_common


def reset_inspector(plot):
    """ Hides the scatter inspector until the user clicks again.
    """
    overlays = plot.plots["scatter_events"][0].overlays
    overlays[0].visible = False


def scatter_plot(measurement,
                 axScatter=None, isoel=None, 
                 square=True, 
                 panzoom=True, select=True):
    """ Plot scatter plot for two axes of an RTDC measurement
    
    Parameters
    ----------
    measurement : instance of RTDS_DataSet
        Contains measurement data.
    axScatter : instance of matplotlib `Axis`
        Plotting axis for the scatter data.
    isoel : list for line plot
        Manually selected isoelastics to plot. Defaults to None.
        If no isoelastics are found, then a warning is raised.
    square : bool
        The plot has square shape.
    panzoom : bool
        Add panning and zooming tools.
    select : bool
        Add point selection tool.
    """
    mm = measurement
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()
    # Plotting area
    plotfilters = mm.config.copy()["plotting"]
    marker_size = plotfilters["scatter marker size"]
    
    # Commence plotting
    if axScatter is not None:
        raise NotImplementedError("Tell Chaco to reuse plots?")
        #plt.figure(1)
        #axScatter = plt.axes()

    scalex = mm.config["Plotting"]["Scale X"].lower()
    scaley = mm.config["Plotting"]["Scale Y"].lower()

    pd = ca.ArrayPlotData()
    
    sc_plot = ca.Plot(pd)
    sc_plot.id = mm.identifier

    ## Add isoelastics
    if mm.config["plotting"]["isoelastics"]:
        if isoel is None:
            chansize = mm.config["general"]["channel width"]
            #plotdata = list()
            # look for isoelastics:
            for key in list(isoelastics.keys()):
                if float(key.split("um")[0]) == chansize > 0:
                    plotdict = isoelastics[key]
                    for key2 in list(plotdict.keys()):
                        if key2 == "{} {}".format(xax, yax):
                            isoel = plotdict[key2]
        if isoel is None:
            warnings.warn("Could not find matching isoelastics for"+
                          " Setting: x={} y={}, Channel width: {}".
                          format(xax, yax, chansize))
        else:
            for ii, data in enumerate(isoel):
                x_key = 'isoel_x'+str(ii)
                y_key = 'isoel_y'+str(ii)
                #
                # # Crop data points outside of the plotting area
                # #data = crop_linear_data(data, areamin, areamax, circmin, circmax)
                #
                pd.set_data(x_key, data[:,0])
                pd.set_data(y_key, data[:,1])
                sc_plot.plot((x_key, y_key), color="gray",
                              index_scale=scalex, value_scale=scaley)

    # Display numer of events
    elabel = ca.PlotLabel(text="",
                          component=sc_plot,
                          vjustify="bottom",
                          hjustify="right",
                          name="events")
    elabel.id = "event_label_"+mm.identifier
    sc_plot.overlays.append(elabel)

    # Set content of scatter plot
    set_scatter_data(sc_plot, mm)

    plot_kwargs = {
                   "name": "scatter_events",
                   "marker": "square",
                   #"fill_alpha": 1.0,
                   "marker_size": int(marker_size),
                   "outline_color": "transparent",
                   "line_width": 0,
                   "bgcolor": "white",
                   "index_scale": scalex,
                   "value_scale": scaley,
                    }

    # Create the KDE plot
    if plotfilters["KDE"].lower() == "none":
        # Single-color plot
        plot_kwargs["data"] = ("index", "value")
        plot_kwargs["type"] = "scatter"
        plot_kwargs["color"] = "black"
    else:
        # Plots with density
        plot_kwargs["data"] = ("index", "value", "color")
        plot_kwargs["type"] = "cmap_scatter"
        plot_kwargs["color_mapper"] = ca.jet

    # Excluded events
    plot_kwargs_excl = plot_kwargs.copy()
    plot_kwargs_excl["name"] = "excluded_events"
    plot_kwargs_excl["data"] = ("excl_index", "excl_value")
    plot_kwargs_excl["type"] = "scatter"
    plot_kwargs_excl["color"] = 0x929292
    if pd.get_data("excl_index") is not None:
        sc_plot.plot(**plot_kwargs_excl)

    # Plot colored points on top of excluded events
    if pd.get_data("index") is not None:
        sc_plot.plot(**plot_kwargs)

    # Axes
    left_axis = ca.PlotAxis(sc_plot, orientation='left',
                            title=dfn.axlabels[yax],
                            tick_generator=plot_common.MyTickGenerator())
    
    bottom_axis = ca.PlotAxis(sc_plot, orientation='bottom',
                              title=dfn.axlabels[xax],
                              tick_generator=plot_common.MyTickGenerator())
    # Show log scale only with 10** values (#56)
    sc_plot.index_axis.tick_generator=plot_common.MyTickGenerator()
    sc_plot.value_axis.tick_generator=plot_common.MyTickGenerator()
    sc_plot.overlays.append(left_axis)
    sc_plot.overlays.append(bottom_axis)

    sc_plot.title = mm.title
    sc_plot.title_font = "modern 12"
    if plotfilters["Scatter Title Colored"]:
        mmlabelcolor = plotfilters["contour color"]
    else:
        mmlabelcolor = "black"
    sc_plot.title_color = mmlabelcolor

    
    # zoom tool
    if panzoom:
        zoom = cta.ZoomTool(sc_plot,
                        tool_mode="box",
                        color="beige",
                        minimum_screen_delta=50,
                        border_color="black",
                        border_size=1,
                        always_on=True,
                        drag_button="right",
                        enable_wheel=True,
                        zoom_factor=1.1)
        sc_plot.tools.append(zoom)
        sc_plot.aspect_ratio = 1
        sc_plot.use_downsampling = True
        
        # pan tool
        pan = cta.PanTool(sc_plot, drag_button="left")
        sc_plot.tools.append(pan)

    # select tool
    if select:
        my_plot = sc_plot.plots["scatter_events"][0]
        my_plot.tools.append(
            cta.ScatterInspector(
                my_plot,
                selection_mode="single",
                persistent_hover=False))
        my_plot.overlays.append(
            ca.ScatterInspectorOverlay(
                my_plot,
                hover_color = "transparent",
                hover_marker_size = int(marker_size*4),
                hover_outline_color = "black",
                hover_line_width = 1,
                selection_marker_size = int(marker_size*1.5),
                selection_outline_color = "black",
                selection_line_width = 1,
                selection_color = "purple")
            )


    return sc_plot


def set_scatter_data(plot, mm):
    plotfilters = mm.config.copy()["plotting"]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()
    
    if mm.config["filtering"]["enable filters"]:
        x0 = mm[dfn.cfgmaprev[xax]][mm._filter]
    else:
        # filtering disabled
        x0 = mm[dfn.cfgmaprev[xax]]

    downsample = plotfilters["downsampling"]*plotfilters["downsample events"]

    a = time.time()
    lx = x0.shape[0]
    x, y = mm.get_downsampled_scatter(xax=xax, yax=yax, downsample=downsample)
    if lx == x.shape:
        positions = None
    else:
        print("...Downsampled from {} to {} in {:.2f}s".format(lx, x.shape[0], time.time()-a))
        positions = np.vstack([x.ravel(), y.ravel()])


    kde_type = mm.config["plotting"]["kde"].lower()
    kde_kwargs = plot_common.get_kde_kwargs(x=x, y=y, kde_type=kde_type,
                                            xacc=mm.config["plotting"]["kde accuracy "+xax],
                                            yacc=mm.config["plotting"]["kde accuracy "+yax])
    
    a = time.time()
    density = mm.get_kde_scatter(xax=xax, yax=yax, positions=positions,
                                 kde_type=kde_type, kde_kwargs=kde_kwargs)
    print("...KDE scatter time {}: {:.2f}s".format(kde_type, time.time()-a))
    
    pd = plot.data
    pd.set_data("index", x)
    pd.set_data("value", y)
    pd.set_data("color", density)

    # Plot filtered data in grey
    if (plotfilters["Scatter Plot Excluded Events"] and
        mm._filter.sum() != len(mm)):
        mm.apply_filter()
        # determine the number of points we are allowed to add
        if downsample:
            # respect the maximum limit of plotted events
            excl_num = int(downsample - np.sum(mm._filter))
            excl_num *= (excl_num>0)
        else:
            # plot all excluded events
            excl_num = np.sum(~mm._filter)
    
        excl_x = mm[dfn.cfgmaprev[xax]][~mm._filter][:excl_num]
        excl_y = mm[dfn.cfgmaprev[yax]][~mm._filter][:excl_num]

        pd.set_data("excl_index", excl_x)
        pd.set_data("excl_value", excl_y)
    else:
        pd.set_data("excl_index", [])
        pd.set_data("excl_value", [])
    
    # Update overlays
    for ol in plot.overlays:
        if ol.id == "event_label_"+mm.identifier:
            # Set events label
            if plotfilters["show events"]:
                oltext = "{} events".format(np.sum(mm._filter))
            else:
                oltext = ""
            ol.text = oltext

    # Density, as returned by dclab contains `nans` where x or y
    # is nan or inf. Use this information to set the plot limits.
    bad = np.isnan(density)

    # Set x-y limits
    xlim = plot.index_mapper.range
    xmin = mm.config["plotting"][xax+" min"]
    xmax = mm.config["plotting"][xax+" max"]
    if xmin == xmax:
        xmin = x[~bad].min()
        xmax = x[~bad].max()
    xlim.low = xmin
    xlim.high = xmax

    ylim = plot.value_mapper.range
    ymin = mm.config["plotting"][yax+" min"]
    ymax = mm.config["plotting"][yax+" max"]
    if ymin == ymax:
        ymin = y[~bad].min()
        ymax = y[~bad].max()
    ylim.low = ymin
    ylim.high = ymax
