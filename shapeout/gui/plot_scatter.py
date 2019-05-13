#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - scatter plot methods"""
from __future__ import division, unicode_literals

import time

import chaco.api as ca
import chaco.tools.api as cta
from dclab import definitions as dfn
import numpy as np

from . import plot_common


def reset_inspector(plot):
    """ Hides the scatter inspector until the user clicks again.
    """
    overlays = plot.plots["scatter_events"][0].overlays
    overlays[0].visible = False


def scatter_plot(measurement,
                 axScatter=None,
                 square=True, 
                 panzoom=True, select=True):
    """Plot scatter plot for two axes of an RT-DC measurement
    
    Parameters
    ----------
    measurement : RTDCBase
        Contains measurement data.
    axScatter : instance of matplotlib `Axis`
        Plotting axis for the scatter data.
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

    scalex = mm.config["plotting"]["scale x"].lower()
    scaley = mm.config["plotting"]["scale y"].lower()

    pd = ca.ArrayPlotData()
    
    sc_plot = ca.Plot(pd)
    sc_plot.id = mm.identifier

    ## Add isoelastics
    isoel = plot_common.get_isoelastics(mm)
    if isoel:
        for ii, data in enumerate(isoel):
            x_key = 'isoel_x'+str(ii)
            y_key = 'isoel_y'+str(ii)
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

    plot_kwargs = {"name": "scatter_events",
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
                            title=dfn.feature_name2label[yax],
                            tick_generator=plot_common.MyTickGenerator())
    
    bottom_axis = ca.PlotAxis(sc_plot, orientation='bottom',
                              title=dfn.feature_name2label[xax],
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
                persistent_hover=False
                )
            )
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
                selection_color = "purple"
                )
            )


    return sc_plot


def set_scatter_data(plot, mm):
    plotfilters = mm.config.copy()["plotting"]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()

    scalex = mm.config["plotting"]["scale x"].lower()
    scaley = mm.config["plotting"]["scale y"].lower()

    x0 = mm[xax][mm.filter.all]

    downsample = plotfilters["downsampling"]*plotfilters["downsample events"]

    a = time.time()
    lx = x0.shape[0]
    x, y = mm.get_downsampled_scatter(xax=xax,
                                      yax=yax,
                                      downsample=downsample,
                                      xscale=scalex,
                                      yscale=scaley,
                                      )
    if lx == x.shape:
        positions = None
    else:
        print("...Downsampled from {} to {} in {:.2f}s".format(lx, x.shape[0], time.time()-a))
        positions = np.vstack([x.ravel(), y.ravel()])


    kde_type = mm.config["plotting"]["kde"].lower()

    kde_kwargs = plot_common.get_kde_kwargs(
        x=x,
        y=y,
        kde_type=kde_type,
        xacc=mm.config["plotting"]["kde accuracy "+xax],
        yacc=mm.config["plotting"]["kde accuracy "+yax])
    
    a = time.time()
    density = mm.get_kde_scatter(xax=xax,
                                 yax=yax,
                                 positions=positions,
                                 xscale=scalex,
                                 yscale=scaley,
                                 kde_type=kde_type,
                                 kde_kwargs=kde_kwargs,
                                 )
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
    
        excl_x = mm[xax][~mm._filter][:excl_num]
        excl_y = mm[yax][~mm._filter][:excl_num]

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
