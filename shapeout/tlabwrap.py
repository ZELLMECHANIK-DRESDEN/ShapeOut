#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - more functionalities for dclab

"""

# Chaco imports
import chaco.api as ca
import chaco.tools.api as cta

from dclab import *  # @UnusedWildImport
from util import findfile

from scipy import stats


from chaco.color_mapper import ColorMapper

def darkjet(myrange, **traits):
    """ Generator function for the 'darkjet' colormap. """
    _data = {'red': ((0., 0, 0), (0.35, 0.0, 0.0), (0.66, .3, .3), (0.89, .4, .4),
    (1, 0.5, 0.5)),
    'green': ((0., 0.0, 0.0), (0.125, .1, .10), (0.375, .4, .4), (0.64,.3, .3),
    (0.91,0.2,0.2), (1, 0, 0)),
    'blue': ((0., 0.7, 0.7), (0.11, .5, .5), (0.34, .4, .4), (0.65, 0, 0),
    (1, 0, 0))}
    return ColorMapper.from_segment_map(_data, range=myrange, **traits)


class Analysis(object):
    """ An object that stores several RTDC data sets and useful methods
    
    This object contains
     - RTDC data sets
     - common configuration parameters of the data sets
     - Plotting parameters
    """
    def __init__(self, data):
        """ Analysis data object.
        """
        self.measurements = list()
        if isinstance(data, list):
            # New analysis
            for f in data:
                if os.path.exists(unicode(f)):
                    # filename
                    self.measurements.append(RTDC_DataSet(f))
                else:
                    # RTDC data set
                    self.measurements.append(f)
        elif isinstance(data, (unicode, str)) and os.path.exists(data):
            # We are opening a session
            self._ImportDumped(data)
        else:
            raise ValueError("Argument not an index file or list of"+\
                             " .tdms files: {}".format(data))

    def _ImportDumped(self, indexname):
        """ Loads data from index file as saved using `self.DumpData`.
        """
        ## Read index file and locate tdms file.
        thedir = os.path.dirname(indexname)
        # Load polygons before importing any data
        polygonfile = os.path.join(thedir, "PolygonFilters.poly")
        PolygonFilter.clear_all_filters()
        if os.path.exists(polygonfile):
            PolygonFilter.import_all(polygonfile)
        # import configurations
        datadict = dfn.LoadConfiguration(indexname, capitalize=False)
        keys = list(datadict.keys())
        for key in keys:
            data = datadict[key]
            name = codecs.escape_decode(data["name"])[0]
            fdir = codecs.escape_decode(data["fdir"])[0]
            tloc = os.path.join(fdir, name)
            mm = RTDC_DataSet(tloc)
            mmhashes = [h[1] for h in mm.file_hashes]
            newhashes = [ data["tdms hash"], data["camera.ini hash"],
                          data["para.ini hash"]
                        ]
            if mmhashes != newhashes:
                raise ValueError("Hashes don't match for file {}.".
                                 format(tloc))
            cfg = dfn.LoadConfiguration(os.path.join(thedir, 
                               codecs.escape_decode(data["config"])[0]))
            mm.UpdateConfiguration(cfg)
            self.measurements.append(mm)

    def DumpData(self, directory, fullout=False):
        """ Dumps all the data from the analysis to a `directory`
        
        Returns a list of filenames that are required to restore this
        analysis. The "index.txt" contains the relative paths to all
        configuration files.
        """
        indexname = os.path.join(directory, "index.txt")
        # Create Index file
        out = ["# ShapeOut Measurement Index"]
        
        i = 0
        for mm in self.measurements:
            i += 1
            ident = "{}_{}".format(i,mm.name)
            mmdir = os.path.join(directory, ident)
            while True:
                g=0
                if os.path.exists(mmdir):
                    mmdir = mmdir+str(g)
                    ident = os.path.split(mmdir)[1]
                    g += 1
                else:
                    break
            os.mkdir(mmdir)
            out.append("[{}]".format(ident))
            out.append("tdms hash = "+mm.file_hashes[0][1])
            out.append("camera.ini hash = "+mm.file_hashes[1][1])
            out.append("para.ini hash = "+mm.file_hashes[2][1])
            out.append("name = "+mm.name+".tdms")
            out.append("fdir = "+mm.fdir)
            # Save configurations
            cfgfile = os.path.join(mmdir, "config.txt")
            SaveConfiguration(cfgfile, mm.Configuration)
            out.append("config = {}".format(os.path.relpath(cfgfile,
                                                            directory)))
            
            
            if fullout:
                # create directory that contains tdms and ini files
                
                ## create copy function that works on all oses!
                raise NotImplementedError("Unable to copy files!")

            out.append("")
            
        for i in range(len(out)):
            out[i] = codecs.escape_encode(str(out[i]))[0]+"\r\n"
        
        index = codecs.open(indexname, "w", "utf-8")
        index.writelines(out)
        index.close()
        
        # Dump polygons
        if len(PolygonFilter.instances) > 0:
            PolygonFilter.save_all(os.path.join(directory,
                                            "PolygonFilters.poly"))
        return indexname

    def ForceSameDataSize(self):
        """
        Force all measurements to have the same filtered size by setting
        the minimum possible value for ["Filtering"]["Limit Events"] and
        return that size.
        """
        # Reset limit filtering to get the correct number of events
        # This value will be overridden in the end.
        cfgreset = {"Filtering":{"Limit Events":0}}
        # This also calls ApplyFilter and comutes clean filters
        self.SetParameters(cfgreset)
        
        # Get minimum size
        minsize = np.inf
        for m in self.measurements:
            minsize = min(minsize, np.sum(m._filter))
        cfgnew = {"Filtering":{"Limit Events":minsize}}
        self.SetParameters(cfgnew)
        return minsize
        

    def GetPlotAxes(self, mid=0):
        #return 
        p = self.GetParameters("Plotting", mid)
        return [p["Axis X"], p["Axis Y"]]

    def GetPlotGeometry(self, mid=0):
        p = self.GetParameters("Plotting", mid)
        return (int(p["Rows"]), int(p["Columns"]),
                int(p["Contour Plot"]), int(p["Legend Plot"]))
                
    def GetCommonParameters(self, key):
        """
        For as key (e.g. "Filtering") find all parameters that are given
        for every measurement in the analysis.
        """
        retdict = dict()
        if self.measurements[0].Configuration.has_key(key):
            s = set(self.measurements[0].Configuration[key].items())
            for m in self.measurements[1:]:
                s2 = set(m.Configuration[key].items())
                s = s & s2
            for item in s:
                retdict[item[0]] = item[1]
        return retdict

    def GetContourColors(self):
        colors = list()
        for mm in self.measurements:
            colors.append(mm.Configuration["Plotting"]["Contour Color"])
        return colors

    def GetStatisticsBasic(self):
        """
        Computes Mean, Avg, etc for all data sets and returns two lists:
        The headings and the values.
        """
        columns_once = [ #these are applied to mm
                        ["Events", lambda mm: np.sum(mm._filter)],
                       ]
        columns = [
                   ["Mean", np.average],
                   ["SD", np.std],
                   ["Mode", lambda x: stats.mode(x)[0][0]],
                   ["Median", np.median],
                   ]
        # heading
        head = ["Data set"]

        for co in columns_once:
            head += [co[0]]

        for ax in self.measurements[0].GetPlotAxes():
            for c in columns:
                head += [" ".join([_(c[0]), _(ax)])+"  "]
        

        datalist = list()
        # loop through measurements
        for mm in self.measurements:
            mmlist = list()
            mmlist.append(mm.title)
            for co in columns_once:
                mmlist.append(co[1](mm))
            # loop through plotted axes
            for ax in mm.GetPlotAxes():
                if mm.Configuration["Filtering"]["Enable Filters"]:
                    x = getattr(mm, dfn.cfgmaprev[ax])[mm._filter]
                else:
                    # filtering disabled
                    x = getattr(mm, dfn.cfgmaprev[ax])
                # compute variable and add to datalist
                for c in columns:
                    mmlist.append(c[1](x))
            datalist.append(mmlist)
        
        return head, datalist

    def PolygonFilterRemove(self, filt):
        """
        Removes a polygon filter from all elements of the analysis.
        """
        for mm in self.measurements:
            try:
                mm.PolygonFilterRemove(filt)
            except ValueError:
                pass


    def SetContourAccuracies(self, points=70):
        """ Set initial (heuristic) accuracies for all plots.
        
        It is not always easy to determine the correct accuracy for
        the contour plots. This method sets these accuracies for the
        active axes for the user. Each axis is divided into `points`
        segments and the length of each segment is then used for the
        accuracy.
        
        All keys of the active axes are changed, e.g.:
          - "Contour Accuracy Area"
          - "Contour Accuracy Defo"
        
        Note that the accuracies are not updated when the key
        ["Plotting"]["Contour Fix Scale"] is set to `True` for the
        first measurement of the analysis.
        """
        # check if updating is disabled:
        if self.measurements[0].Configuration["Plotting"]["Contour Fix Scale"]:
            return
        
        if len(self.measurements) > 1:
            # first create dictionary with min/max keys
            minmaxdict = dict()
            for name in dfn.uid:
                minmaxdict["{} Min".format(name)] = list()
                minmaxdict["{} Max".format(name)] = list()
                
            for mm in self.measurements:
                # uid is defined in definitions
                for name in dfn.uid:
                    if hasattr(mm, dfn.cfgmaprev[name]):
                        att = getattr(mm, dfn.cfgmaprev[name])
                        minmaxdict["{} Min".format(name)].append(att.min())
                        minmaxdict["{} Max".format(name)].append(att.max())
            # set contour accuracy for every element
            for name in dfn.uid:
                atmax = np.average(minmaxdict["{} Max".format(name)])
                atmin = np.average(minmaxdict["{} Min".format(name)])
                acc = (atmax-atmin)/points
                # round to 2 significant digits
                acg = float("{:.1e}".format(acc))
                acm = float("{:.1e}".format(acc*2))
                for mm in self.measurements:
                    mm.Configuration["Plotting"]["Contour Accuracy {}".format(name)] = acg
                    mm.Configuration["Plotting"]["KDE Multivariate {}".format(name)] = acm
        
    def SetContourColors(self, colors=None):
        """ Sets the contour colors
        """
        if len(self.measurements) > 1:
            if colors is None or len(colors) < len(self.measurements):
                # set colors
                colormap=darkjet(ca.DataRange1D(low=0, high=1),
                                steps=len(self.measurements))
                colors=colormap.color_bands
                newcolors = list()
                for color in colors:
                    color = [ float(c) for c in color ]
                    newcolors.append(color)
                colors = newcolors
            for i, mm in enumerate(self.measurements):
                mm.Configuration["Plotting"]["Contour Color"] = colors[i]

    def GetUncommonParameters(self, key):
        # Get common parameters first:
        com = self.GetCommonParameters(key)
        retdict = dict()
        if self.measurements[0].Configuration.has_key(key):
            s = set(self.measurements[0].Configuration[key].items())
            uncom = set(com.items()) ^ s
            for m in self.measurements[1:]:
                s2 = set(m.Configuration[key].items())
                uncom2 = set(com.items()) ^ s2
                
                newuncom = dict()
                uncom.symmetric_difference_update(uncom2)
                for _i in range(len(uncom)):
                    item = uncom.pop()
                    newuncom[item[0]] = None
                uncom = set(newuncom.items())
                    
            for item in uncom:
                vals = list()
                for m in self.measurements:
                    if m.Configuration[key].has_key(item[0]):
                        vals.append(m.Configuration[key][item[0]])
                    else:
                        vals.append(None)
                        warnings.warn(
                          "Measurement {} might be corrupt!".format(m.name))
                retdict[item[0]] = vals
        return retdict        

    def GetUnusableAxes(self):
        """ 
        Unusable axes are axes that are not shared by all
        measurements. A measurement does not have an axis, if all
        values along that axis are zero.

        See Also
        --------
        GetUsableAxes
        """
        unusable = []
        for ax in dfn.uid:
            for mm in self.measurements:
                # Get the attribute name for the axis
                atname = dfn.cfgmaprev[ax]
                if np.sum(np.abs(getattr(mm, atname))) == 0:
                    unusable.append(ax)
                    break
        return unusable


    def GetUsableAxes(self):
        """ 
        Usable axes are axes that are shared by all measurements
        A measurement does not have an axis, if all values along
        that axis are zero.

        See Also
        --------
        GetUnusableAxes
        """
        unusable = self.GetUnusableAxes()
        usable = []
        for ax in dfn.uid:
            if not ax in unusable:
                usable.append(ax)
        return usable


    def GetNames(self):
        """ Returns the names of all measurements """
        names = list()
        for mm in self.measurements:
            names.append(mm.name)
        return names

    def GetParameters(self, key, mid=0, filter_for_humans=True):
        """ Get parameters that all measurements share.
        """
        conf = copy.deepcopy(self.measurements[mid].Configuration[key])
        # remove generally ignored items from config
        for k in list(conf.keys()):
            for ax in IGNORE_AXES:
                if k.startswith(ax) or k.endswith(ax):
                    conf.pop(k)
        # remove axes that are not owned by all measurements
        for k in list(conf.keys()):
            if k.endswith("Min") or k.endswith("Max"):
                ax = k[:-4]
                if ax in self.GetUnusableAxes():
                    conf.pop(k)
        return conf

    def GetTDMSFilenames(self):
        names = list()
        for mm in self.measurements:
            names.append(mm.tdms_filename)
        return names

    def GetTitles(self):
        """ Returns the titles of all measurements """
        titles = list()
        for mm in self.measurements:
            titles.append(mm.title)
        return titles


    def SetParameters(self, newcfg):
        """ updates the RTDC_DataSet configuration

        """
        newcfg = copy.deepcopy(newcfg)
        # prevent applying indivual things to all measurements
        ignorelist = ["Contour Color"]
        for key in newcfg.keys():
            for skey in newcfg[key].keys():
                if skey in ignorelist:
                    newcfg[key].pop(skey)
                    
        # update configuration
        for i in range(len(self.measurements)):
            self.measurements[i].UpdateConfiguration(newcfg)



def CreateContourPlot(measurements, xax="Area", yax="Defo", levels=.5,
                      axContour=None, isoel=None,
                      wxtext=False, square=True):
    """ Plot contour for two axes of an RTDC measurement
    
    Parameters
    ----------
    measurement : instance of RTDS_DataSet
        Contains measurement data.
    xax : str
        x-Axis to plot (see `librtdc.dfn.cfgmap`)
    yax : str
        y-Axis to plot (see `librtdc.dfn.cfgmap`)
    levels : float or list of floats in interval (0,1)
        Plot the contour at that particular level from the maximum (1).
    axContour : instance of matplotlib `Axis`
        Plotting axis for the contour.
    isoel : list for line plot
        Manually selected isoelastics to plot. Defaults to None.
        If no isoelastics are found, then a warning is raised.
    square : bool
        The plot has square shape.
    """

    mm = measurements[0]
    
    
    
    # Plotting area
    plotfilters = mm.Configuration["Plotting"]
    
   
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
    if axContour is not None:
        raise NotImplementedError("Tell Chaco to reuse plots?")
        #plt.figure(1)
        #axScatter = plt.axes()


    pd = ca.ArrayPlotData()
    contour_plot = ca.Plot(pd)

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
                # # Crop data events outside of the plotting area
                # #data = crop_linear_data(data, areamin, areamax, circmin, circmax)
                #
                pd.set_data(x_key, data[:,0])
                pd.set_data(y_key, data[:,1])
                contour_plot.plot((x_key, y_key), color="gray")


    #colors = [ "".join(map(chr, np.array(c[:3]*255,dtype=int))).encode('hex') for c in colors ]
    if not isinstance(levels, list):
        levels = [levels]

    for mm, ii in zip(measurements, range(len(measurements))):
        
        a=time.time()
        (X,Y,density) = mm.GetKDE_Contour(yax=yax, xax=xax)
        print("Contour computation time", time.time() -a)
        
        cname = "con_{}_{}_{}".format(mm.name, mm.file_hashes[0][1], ii)

        pd.set_data(cname, density)

        #plt.contour(x,y,density,1,colors=[c],label=name,linewidths=[2.5],zorder=5)
        plev = [np.max(density)*i for i in levels]

        if len(plev) == 2:
            styles = ["dot", "solid"]
        else:
            styles = "solid"

        
        # contour widths
        if "Contour Width" in mm.Configuration["Plotting"]:
            cwidth = mm.Configuration["Plotting"]["Contour Width"]
        else:
            cwidth = 1.2
        
        contour_plot.contour_plot(cname,
                                  type="line",
                                  xbounds = (X[0][0], X[0][-1]),
                                  ybounds = (Y[0][0], Y[-1][0]),
                                  levels = plev,
                                  colors = mm.Configuration["Plotting"]["Contour Color"],
                                  styles = styles,
                                  widths = [cwidth*.7, cwidth] # make outer lines slightly smaller
                                  )
        
        
    # Set x-y limits
    xlim = contour_plot.index_mapper.range
    ylim = contour_plot.value_mapper.range
    xlim.low = areamin
    xlim.high = areamax
    ylim.low = circmin
    ylim.high = circmax


    # Axes
    left_axis = ca.PlotAxis(contour_plot, orientation='left',
                            title=dfn.axlabels[yax])
    bottom_axis = ca.PlotAxis(contour_plot, orientation='bottom',
                              title=dfn.axlabels[xax])
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


def CreateLegendPlot(measurements, title_font="modern 12",
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
                        label_position="right",
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


def CreateScatterPlot(measurement, xax="Area", yax="Defo",
                      axScatter=None, isoel=None, 
                      square=True, 
                      downsampling=None, downsample_events=None,
                      panzoom=True, select=True):
    """ Plot scatter plot for two axes of an RTDC measurement
    
    Parameters
    ----------
    measurement : instance of RTDS_DataSet
        Contains measurement data.
    xax : str
        x-Axis to plot (see `librtdc.dfn.cfgmap`)
    yax : str
        y-Axis to plot (see `librtdc.dfn.cfgmap`)
    kde_type : str
        Type of KDE estimate. Can be "gauss" or "multivariate".
    axScatter : instance of matplotlib `Axis`
        Plotting axis for the scatter data.
    isoel : list for line plot
        Manually selected isoelastics to plot. Defaults to None.
        If no isoelastics are found, then a warning is raised.
    square : bool
        The plot has square shape.
    downsampling : int or None
        Filter dots that are overdrawn by others (saves time).
        If set to None then
        Configuration["Plotting"]["Downsampling"] is used.
        Chaco does not yet have this implemented.
    downsample_events : int or None
        Number of events to draw in the down-sampled plot. This number
        is either 
        - >=1: limit total number of events drawn
        - <1: only perform 1st downsampling step with grid
        If set to None, then
        Configuration["Plotting"]["Downsample Events"] will be used.
    panzoom : bool
        Add panning and zooming tools.
    select : bool
        Add point selection tool.
    """
    mm = measurement

    # Plotting area
    plotfilters = mm.Configuration["Plotting"].copy()
    marker_size = plotfilters["Scatter Marker Size"]
    
    if downsampling is None:
        downsampling = plotfilters["Downsampling"]
        
    if downsample_events is None:
        downsample_events = plotfilters["Downsample Events"]
    
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

    if mm.Configuration["Filtering"]["Enable Filters"]:
        x = getattr(mm, dfn.cfgmaprev[xax])[mm._filter]
        y = getattr(mm, dfn.cfgmaprev[yax])[mm._filter]
    else:
        # filtering disabled
        x = getattr(mm, dfn.cfgmaprev[xax])
        y = getattr(mm, dfn.cfgmaprev[yax])
    
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


    pd = ca.ArrayPlotData()
    scatter_plot = ca.Plot(pd)

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
                scatter_plot.plot((x_key, y_key), color="gray")


    pd.set_data("index", x)
    pd.set_data("value", y)
    pd.set_data("color", density)
    
    # Create the plot
    scatter_plot.plot(("index", "value", "color"),
              type="cmap_scatter",
              name="my_plot",
              #color_mapper=ca.jet,
              color_mapper=ca.jet,
              marker = "square",
              #fill_alpha = 1.0,
              marker_size = int(marker_size),
              outline_color = "transparent",
              line_width = 0,
              bgcolor = "white")


    # Set x-y limits
    xlim = scatter_plot.index_mapper.range
    ylim = scatter_plot.value_mapper.range
    xlim.low = areamin
    xlim.high = areamax
    ylim.low = circmin
    ylim.high = circmax


    # Axes
    left_axis = ca.PlotAxis(scatter_plot, orientation='left',
                            title=dfn.axlabels[yax])
    bottom_axis = ca.PlotAxis(scatter_plot, orientation='bottom',
                              title=dfn.axlabels[xax])
    scatter_plot.overlays.append(left_axis)
    scatter_plot.overlays.append(bottom_axis)

    scatter_plot.title = mm.title
    scatter_plot.title_font = "modern 12"
    if mm.Configuration["Plotting"]["Scatter Title Colored"]:
        mmlabelcolor = mm.Configuration["Plotting"]["Contour Color"]
    else:
        mmlabelcolor = "black"
    scatter_plot.title_color = mmlabelcolor

    # Display numer of events
    if mm.Configuration["Plotting"]["Show Events"]:
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
        my_plot = scatter_plot.plots["my_plot"][0]
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

        
def GetTDMSTreeGUI(directories):
    """ Returns projects (folders) and measurements therein
    
    This is a convenience function for the GUI
    """
    if not isinstance(directories, list):
        directories = [directories]
    
    directories = np.unique(directories)
    
    pathdict = dict()
    treelist = list()
    
    for directory in directories:
        files = GetTDMSFiles(directory)

        #cols = [_("Measurement"), _("Creation Date")]
        #to = os.path.getctime(f)
        #t = time.strftime("%Y-%m-%d %H:%M", time.gmtime(to))
        cols = ["Measurement"]

        for f in files:
            if not IsFullMeasurement(f):
                # Ignore measurements that have missing camera or para inis.
                continue
            path, name = os.path.split(f)
            # try to find the path in pathdict
            if pathdict.has_key(path):
                i = pathdict[path]
            else:
                treelist.append(list())
                i = len(treelist)-1
                pathdict[path] = i
                # The first element of a tree contains the measurement name
                project = GetProjectNameFromPath(path)
                treelist[i].append((project, path))
            # Get data from filename
            mx = name.split("_")[0]
            if GetRegion(f).lower() in ["reservoir"]:
                #parcfg = LoadConfiguration(stem+"_para.ini")
                dn = u"{} {}".format(mx, GetRegion(f))
            else:
                # outlet (flow rate is not important)
                dn = u"{} {}  {} µls⁻¹".format(mx, GetRegion(f),
                                               GetFlowRate(f))
                                   
            treelist[i].append((dn, f))
        
    return treelist, cols


def IsFullMeasurement(fname):
    """ Checks for existence of ini files and returns False if some
        files are missing.
    """
    path, name = os.path.split(fname)
    mx = name.split("_")[0]
    stem = os.path.join(path, mx)
    if ( (not os.path.exists(stem+"_para.ini")) or
         (not os.path.exists(stem+"_camera.ini")) or
         (not os.path.exists(fname))                ):
        return False
    else:
        return True


def GetDefaultConfiguration(key=None):
    config = dfn.LoadDefaultConfiguration()
    config = dfn.LoadConfiguration(cfg_file, config)
    if key is not None:
        return config[key]
    else:
        return config


def GetFlowRate(fname):
    """ Get the flow rate for a tdms file in [ul/s]. 
    
    """
    path, name = os.path.split(fname)
    mx = name.split("_")[0]
    stem = os.path.join(path, mx)
    if os.path.exists(stem+"_para.ini"):
        camcfg = dfn.LoadConfiguration(stem+"_para.ini")
        return camcfg["General"]["Flow Rate [ul/s]"]
    else:
        # analyze the filename
        warnings.warn("{}: trying to manually find flow rate.".
                       format(fname))
        flrate = float(fname.split("ul_s")[0].split("_")[-1])
        return float(flrate)


def GetRegion(fname):
    """ Get the region (inlet/outlet) for a measurement
    """
    path, name = os.path.split(fname)
    mx = name.split("_")[0]
    stem = os.path.join(path, mx)
    if os.path.exists(stem+"_para.ini"):
        camcfg = dfn.LoadConfiguration(stem+"_para.ini")
        return camcfg["General"]["Region"].lower()
    else:
        return ""


def LoadIsoelastics(isoeldir, isoels={}):
    """ Load isoelastics from directories.
    
    
    Parameters
    ----------
    isoeldir : absolute path
        Directory containing isoelastics.
    isoels : dict
        Dictionary to update with isoelastics. If not given, a new
        isoelastics dictionary in librtdc format will be created.


    Returns
    -------
    isoels : dict
        New isoelastics dictionary.
    """
    newcurves = dict()
    # First get a list of all possible files
    for root, dirs, files in os.walk(isoeldir):
        for d in dirs:
            if d.startswith("isoel") or d.startswith("isomech"):
                txtfiles = list()
                curdir = os.path.join(root,d)
                filed = os.listdir(curdir)
                for f in filed:
                    if f.endswith(".txt"):
                        txtfiles.append(os.path.join(curdir, f))
                key = (d.replace("isoelastics","").replace("isoel","")
                        .replace("isomechanics","")
                        .replace("isomech","").replace("_"," ").strip())
                counter = 1
                key2 = key
                while True:
                    if isoels.has_key(key2):
                        key2 = key + " "+str(counter)
                        counter += 1
                    else:
                        break
                newcurves[key2] = txtfiles
    
    # Iterate through the files and import curves
    for key in list(newcurves.keys()):
        files = newcurves[key]
        if os.path.split(files[0])[1].startswith("Defo-Area"):
            # Load Matplab-generated AreaVsCircularity Plot
            # It is actually Deformation vs. Area
            isoels[key] = curvedict = dict()
            Plot1 = "Defo Area"
            Plot2 = "Circ Area"
            Plot3 = "Area Defo"
            Plot4 = "Area Circ"
            list1 = list()
            list2 = list()
            list3 = list()
            list4 = list()
            for f in files:
                xy1 = np.loadtxt(f)
                xy2 = 1*xy1
                xy2[:,0] = 1 - xy1[:,0]
                list1.append(xy1)
                list2.append(xy2)
                list3.append(xy1[:,::-1])
                list4.append(xy2[:,::-1])
            curvedict[Plot1] = list1
            curvedict[Plot2] = list2
            curvedict[Plot3] = list3
            curvedict[Plot4] = list4
        else:
            warnings.warn("Unknown isoelastics: {}".format(files[0]))
    
    return isoels


def GetConfigurationKeys(cfgfilename, capitalize=True):
    """
    Load the configuration file and return the list of variables
    in the order they appear.
    """
    with open(cfgfilename, 'r') as f:
        code = f.readlines()
    
    cfglist = list()
    
    for line in code:
        # We deal with comments and empty lines
        # We need to check line length first and then we look for
        # a hash.
        line = line.split("#")[0].strip()
        if len(line) != 0 and not (line.startswith("[") and line.endswith("]")):
            var = line.split("=", 1)[0].strip()
            cfglist.append(var)
    
    return cfglist


def SortConfigurationKeys(cfgkeys):
    """
    Sorts a list of configuration keys according to the appearance in the
    ShapeOut dclab.cfg configuration file.
    
    If items are not present in this file, then the will be sorted according to
    the string value.
    
    This function is used to determine the displayed order of parameters in
    ShapeOut using the configuration file `dclab.cfg`.
    
    `cfgkeys` may be a list of tuples where the first element is the key
    or a list of keys.
    
    This method uses the global variable `cfg_ordered_list` to loookup
    in which order the data should be sorted.
    """
    orderlist = cfg_ordered_list
    
    def compare(x, y):
        """
        Compare keys for sorting.
        """
        if isinstance(x, (list, tuple)):
            x = x[0]
        if isinstance(y, (list, tuple)):
            y = y[0]
        
        if x in orderlist:
            rx = orderlist.index(x)
        else:
            rx = len(orderlist) + 1
        if y in orderlist:
            ry = orderlist.index(y)
        else:
            ry = len(orderlist) + 1
        if rx == ry:
            if x<y:
                ry += 1
            else:
                rx += 1
        return rx-ry

    return sorted(cfgkeys, cmp=compare)


## Overwrite the tlab configuration with our own.
cfg_file = findfile("dclab.cfg")
cfg = dfn.LoadConfiguration(cfg_file, dfn.cfg)
cfg_ordered_list = GetConfigurationKeys(cfg_file)

thispath = os.path.dirname(os.path.realpath(__file__))
isoeldir = findfile("isoelastics")
isoelastics = LoadIsoelastics(os.path.join(thispath, isoeldir))

# Axes that should not be displayed  by Shape Out
IGNORE_AXES = ["AreaPix", "Frame"]
