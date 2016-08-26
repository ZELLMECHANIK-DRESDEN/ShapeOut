#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - scatter plot methods

"""
from __future__ import division, unicode_literals

import chaco.api as ca
import chaco.tools.api as cta

from dclab import *  # @UnusedWildImport

from . import misc
from ..tlabwrap import isoelastics



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
    xax, yax = mm.GetPlotAxes()
    # Plotting area
    plotfilters = mm.Configuration["Plotting"].copy()
    marker_size = plotfilters["Scatter Marker Size"]
    
    # We will pretend as if we are plotting circularity vs. area
    areamin = plotfilters[xax+" Min"]
    areamax = plotfilters[xax+" Max"]
    circmin = plotfilters[yax+" Min"]
    circmax = plotfilters[yax+" Max"]

    if areamin == areamax:
        areamin = getattr(mm, dfn.cfgmaprev[xax]).min()
        areamax = getattr(mm, dfn.cfgmaprev[xax]).max()

    if circmin == circmax:
        circmin = getattr(mm, dfn.cfgmaprev[yax]).min()
        circmax = getattr(mm, dfn.cfgmaprev[yax]).max()

    # Commence plotting
    if axScatter is not None:
        raise NotImplementedError("Tell Chaco to reuse plots?")
        #plt.figure(1)
        #axScatter = plt.axes()

    scalex = mm.Configuration["Plotting"]["Scale X"].lower()
    scaley = mm.Configuration["Plotting"]["Scale Y"].lower()

    pd = ca.ArrayPlotData()
    
    scatter_plot = ca.Plot(pd)
    scatter_plot.id = mm.identifier

    ## Add isoelastics
    if mm.Configuration["Plotting"]["Isoelastics"]:
        if isoel is None:
            chansize = mm.Configuration["General"]["Channel Width"]
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
                scatter_plot.plot((x_key, y_key), color="gray",
                                  index_scale=scalex, value_scale=scaley)

    set_scatter_data(scatter_plot, mm)

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

    if pd.get_data("index") is not None:
        scatter_plot.plot(**plot_kwargs)

    # Excluded events
    if (plotfilters["Scatter Plot Excluded Events"] and
        mm._filter.sum() != mm.time.shape[0]):
        plot_kwargs_excl = plot_kwargs.copy()
        plot_kwargs_excl["name"] = "excluded_events"
        plot_kwargs_excl["data"] = ("excl_index", "excl_value")
        plot_kwargs_excl["type"] = "scatter"
        plot_kwargs_excl["color"] = 0x929292
        if pd.get_data("excl_index") is not None:
            scatter_plot.plot(**plot_kwargs_excl)

    # Set x-y limits
    xlim = scatter_plot.index_mapper.range
    ylim = scatter_plot.value_mapper.range
    xlim.low = areamin
    xlim.high = areamax
    ylim.low = circmin
    ylim.high = circmax

    # Axes
    left_axis = ca.PlotAxis(scatter_plot, orientation='left',
                            title=dfn.axlabels[yax],
                            tick_generator=misc.MyTickGenerator())
    
    bottom_axis = ca.PlotAxis(scatter_plot, orientation='bottom',
                              title=dfn.axlabels[xax],
                              tick_generator=misc.MyTickGenerator())
    # Show log scale only with 10** values (#56)
    scatter_plot.index_axis.tick_generator=misc.MyTickGenerator()
    scatter_plot.value_axis.tick_generator=misc.MyTickGenerator()
    scatter_plot.overlays.append(left_axis)
    scatter_plot.overlays.append(bottom_axis)

    scatter_plot.title = mm.title
    scatter_plot.title_font = "modern 12"
    if plotfilters["Scatter Title Colored"]:
        mmlabelcolor = plotfilters["Contour Color"]
    else:
        mmlabelcolor = "black"
    scatter_plot.title_color = mmlabelcolor

    # Display numer of events
    if plotfilters["Show Events"]:
        elabel = ca.PlotLabel(text="{} events".format(np.sum(mm._filter)),
                              component=scatter_plot,
                              vjustify="bottom",
                              hjustify="right")
        scatter_plot.overlays.append(elabel)
        
    # zoom tool
    if panzoom:
        zoom = cta.ZoomTool(scatter_plot,
                        tool_mode="box",
                        color="beige",
                        minimum_screen_delta=50,
                        border_color="black",
                        border_size=1,
                        always_on=True,
                        drag_button="right",
                        enable_wheel=True,
                        zoom_factor=1.1)
        scatter_plot.tools.append(zoom)
        scatter_plot.aspect_ratio = 1
        scatter_plot.use_downsampling = True
        
        # pan tool
        pan = cta.PanTool(scatter_plot, drag_button="left")
        scatter_plot.tools.append(pan)

    if select:
        my_plot = scatter_plot.plots["scatter_events"][0]
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


    return scatter_plot


def set_scatter_data(plot, mm):
    plotfilters = mm.Configuration["Plotting"].copy()
    xax, yax = mm.GetPlotAxes()
    
    if mm.Configuration["Filtering"]["Enable Filters"]:
        x = getattr(mm, dfn.cfgmaprev[xax])[mm._filter]
        y = getattr(mm, dfn.cfgmaprev[yax])[mm._filter]
    else:
        # filtering disabled
        x = getattr(mm, dfn.cfgmaprev[xax])
        y = getattr(mm, dfn.cfgmaprev[yax])
    
    #downsampling : int or None
    #    Filter events that are overdrawn by others (saves time).
    #    If set to None then
    downsampling = plotfilters["Downsampling"]
    #downsample_events : int or None
    #    Number of events to draw in the down-sampled plot. This number
    #    is either 
    #    - >=1: limit total number of events drawn
    #    - <1: only perform 1st downsampling step with grid
    #    If set to None, then
    downsample_events = plotfilters["Downsample Events"]

    if downsampling:
        lx = x.shape[0]
        x, y = mm.GetDownSampledScatter(
                                    downsample_events=downsample_events
                                    )
        positions = np.vstack([x.ravel(), y.ravel()])
        print("Downsampled from {} to {}".format(lx, x.shape[0]))
    else:
        positions = None

    density = mm.GetKDE_Scatter(yax=yax, xax=xax, positions=positions)

    pd = plot.data
    
    pd.set_data("index", x)
    pd.set_data("value", y)
    pd.set_data("color", density)

    # Plot filtered data in grey
    mm.ApplyFilter()
    # determine the number of points we are allowed to add
    if downsampling:
        # respect the maximum limit of plotted events
        excl_num = int(downsample_events - np.sum(mm._filter))
    else:
        # plot all excluded events
        excl_num = np.sum(~mm._filter)

    excl_x = getattr(mm, dfn.cfgmaprev[xax])[~mm._filter][:excl_num]
    excl_y = getattr(mm, dfn.cfgmaprev[yax])[~mm._filter][:excl_num]
    pd.set_data("excl_index", excl_x)
    pd.set_data("excl_value", excl_y)
        