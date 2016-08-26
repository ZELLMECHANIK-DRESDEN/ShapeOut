#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - more functionalities for dclab

"""
from __future__ import division, unicode_literals

# Chaco imports
import chaco.api as ca
import chaco.tools.api as cta

from dclab import *  # @UnusedWildImport
from dclab.rtdc_dataset import UpdateConfiguration, SaveConfiguration, hashfile
from nptdms import TdmsFile

from util import findfile

from scipy import stats

from chaco.color_mapper import ColorMapper

from .gui import misc


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
    def __init__(self, data, search_path="./"):
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
            # We are opening a session "index.txt" file
            self._ImportDumped(data, search_path=search_path)
        else:
            raise ValueError("Argument not an index file or list of"+\
                             " .tdms files: {}".format(data))

    def _ImportDumped(self, indexname, search_path="./"):
        """ Loads data from index file as saved using `self.DumpData`.
        
        Parameters
        ----------
        indexname : str
            Path to index.txt file
        search_path : str
            Relative search path where to look for tdms files if
            the absolute path stored in index.txt cannot be found.
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
        # The identifier (in brackets []) contains a number before the first
        # underscore "_" which determines the order of the plots:
        keys.sort(key=lambda x: int(x.split("_")[0]))
        for key in keys:
            data = datadict[key]
            tloc = session_get_tdms_file(data, search_path)
            mm = RTDC_DataSet(tloc)
            if "title" in data:
                # title saved starting version 0.5.6.dev6
                mm.title = data["title"]
            mmhashes = [h[1] for h in mm.file_hashes]
            newhashes = [ data["tdms hash"], data["camera.ini hash"],
                          data["para.ini hash"]
                        ]
            if mmhashes != newhashes:
                raise ValueError("Hashes don't match for file {}.".
                                 format(tloc))
            config_file = os.path.join(thedir, data["config"])
            cfg = dfn.LoadConfiguration(config_file)
            
            # Load manually excluded events
            filter_manual_file = os.path.join(os.path.dirname(config_file),
                                              "_filter_manual.npy")
            if os.path.exists(filter_manual_file):
                mm._filter_manual = np.load(os.path.join(filter_manual_file))
            
            mm.UpdateConfiguration(cfg)
            self.measurements.append(mm)
            
    @staticmethod
    def compute_mode(data):
        """ Compute an intelligent value for the mode
        
        The most common value in experimental is not very useful if there
        are a lot of digits after the comma. This method approaches this
        issue by rounding to bin size that is determined by the
        Freedman–Diaconis rule.
        
        Parameters
        ----------
        data : 1d ndarray
            The data for which the mode should be computed.
        
        Returns
        -------
        mode : float
            The mode computed with the Freedman-Diaconis rule.
        """
        # size
        n = data.shape[0]
        # interquartile range
        iqr = np.percentile(data, 75)-np.percentile(data, 25)
        # Freedman–Diaconis
        bin_size = 2 * iqr / n**(1/3)
        
        if bin_size == 0:
            return np.nan
        
        # Add bin_size/2, because we want the center of the bin and
        # not the left corner of the bin.
        databin = np.round(data/bin_size)*bin_size + bin_size/2
        u, indices = np.unique(databin, return_inverse=True)
        mode = u[np.argmax(np.bincount(indices))]
        
        return mode
        

    def DumpData(self, directory, fullout=False, rel_path="./"):
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
            # the directory in the session zip file where all information
            # will be stored:
            mmdir = os.path.join(directory, ident)
            while True:
                # If the directory already exists, append a number to that
                # directory to distinguish different measurements.
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
            try:
                # On Windows we have multiple drive letters and
                # relpath will complain about that if mm.fdir and
                # rel_path are not on the same drive.
                rdir = os.path.relpath(mm.fdir, rel_path)
            except ValueError:
                rdir = "."
            out.append("rdir = "+rdir)
            out.append("title = "+mm.title)
            # Save configurations
            cfgfile = os.path.join(mmdir, "config.txt")
            SaveConfiguration(cfgfile, mm.Configuration)
            out.append("config = {}".format(os.path.relpath(cfgfile,
                                                            directory)))
            
            # save manual filters
            np.save(os.path.join(mmdir, "_filter_manual.npy"), mm._filter_manual)
            
            if fullout:
                # create directory that contains tdms and ini files
                
                ## create copy function that works on all oses!
                raise NotImplementedError("Unable to copy files!")

            out.append("")
            
        for i in range(len(out)):
            out[i] += "\r\n"
        
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

    def GetNames(self):
        """ Returns the names of all measurements """
        names = list()
        for mm in self.measurements:
            names.append(mm.name)
        return names

    def GetPlotAxes(self, mid=0):
        #return 
        p = self.GetParameters("Plotting", mid)
        return [p["Axis X"], p["Axis Y"]]

    def GetPlotGeometry(self, mid=0):
        p = self.GetParameters("Plotting", mid)
        return (int(p["Rows"]), int(p["Columns"]),
                int(p["Contour Plot"]), int(p["Legend Plot"]))

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
                   ["Mode", Analysis.compute_mode],
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
                    try:
                        value = c[1](x)
                    except IndexError:
                        value = np.nan
                    mmlist.append(value)
            datalist.append(mmlist)
        
        return head, datalist

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


    def SetParameters(self, newcfg):
        """ updates the RTDC_DataSet configuration

        """
        newcfg = copy.deepcopy(newcfg)

        # Address issue with faulty contour plot on log scale
        # https://github.com/enthought/chaco/issues/300
        if "Plotting" in newcfg:
            pl = newcfg["Plotting"]
            if (("Scale X" in pl and pl["Scale X"] == "Log") or
                ("Scale Y" in pl and pl["Scale Y"] == "Log")):
                warnings.warn("Disabling contour plot because of chaco issue #300!")
                newcfg["Plotting"]["Contour Plot"] = False

        # prevent applying indivual things to all measurements
        ignorelist = ["Contour Color"]
        for key in newcfg.keys():
            for skey in newcfg[key].keys():
                if skey in ignorelist:
                    newcfg[key].pop(skey)
                    
        # update configuration
        for i in range(len(self.measurements)):
            self.measurements[i].UpdateConfiguration(newcfg)


class Fake_RTDC_DataSet(object):
    """ Provides methods and attributes like RTDC_DataSet, but without
        data.
    
    Needs a `Configuration` (e.g. from an RTDC_DataSet).
    """
    def __init__(self, Configuration):
        for item in dfn.rdv:
            setattr(self, item, np.zeros(10))
        
        self.deform +=1
        self.area_um +=1
        self._filter =  np.ones(10, dtype=bool)
        self.Configuration = copy.deepcopy(Configuration)
        self.Configuration["Plotting"]["Contour Color"] = "white"
        self.name = ""
        self.tdms_filename = ""
        self.title = ""
        self.file_hashes = [["None", "None"]]
        self.identifier = "None"

    def GetDownSampledScatter(self, *args, **kwargs):
        return np.zeros(10), np.zeros(10)
        
    def GetKDE_Contour(self, yax="Defo", xax="Area"):
        return [[np.zeros(1)]*3]*3
    
    def GetKDE_Scatter(self, yax="Defo", xax="Area", positions=None):
        return np.zeros(10)

    def UpdateConfiguration(self, newcfg):
        UpdateConfiguration(self.Configuration, newcfg)

    def GetPlotAxes(self):
        return ["Defo", "Area"]
    
    def ApplyFilter(self):
        pass


def session_check_index(indexname, search_path="./"):
    """ Check a session file index for existance of all measurement files
    """
    missing_files = []
    
    datadict = dfn.LoadConfiguration(indexname, capitalize=False)
    keys = list(datadict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    keys.sort(key=lambda x: int(x.split("_")[0]))
    for key in keys:    
        data = datadict[key]
        tdms = session_get_tdms_file(data, search_path)
        if not os.path.exists(tdms):
            missing_files.append([key, tdms, data["tdms hash"]])
    
    messages = {"missing tdms": missing_files}
    return messages


def session_get_tdms_file(index_dict,
                          search_path="./",
                          errors="ignore"):
    """ Get the tdms file from entries in the index dictionary
    
    The index dictionary is created from each entry in the
    the index.txt file and contains the keys "name", "fdir", and
    since version 0.6.1 "rdir".
    
    If the file cannot be found on the file system, then a warning
    is issued if `errors` is set to "ignore", otherwise an IOError
    is raised.
    
    """
    found = False
    tdms1 = os.path.join(index_dict["fdir"], index_dict["name"])
    
    if os.path.exists(tdms1):
        found = tdms1
    else:
        if "rdir" in index_dict:
            # try to find relative path
            sdir = os.path.abspath(search_path)
            ndir = os.path.abspath(os.path.join(sdir, index_dict["rdir"]))
            tdms2 = os.path.join(ndir, index_dict["name"])
            if os.path.exists(tdms2):
                found = tdms2
    
    if not found:
        if errors == "ignore":
            warnings.warn("Could not find file: {}".format(tdms1))
            found = tdms1
        else:
            raise IOError("Could not find file: {}".format(tdms1))

    return found


def session_update_index(indexname, updict={}):
    datadict = dfn.LoadConfiguration(indexname, capitalize=False)
    for key in updict:
        datadict[key].update(updict[key])
    SaveConfiguration(indexname, datadict)
    

def search_hashed_tdms(tdms_file, tdms_hash, directories):
    """ Search `directories` for `tdms_file` with matching `tdms_hash`
    """
    tdms_file = os.path.basename(tdms_file)
    for adir in directories:
        for root, _ds, fs in os.walk(adir):
            if tdms_file in fs:
                this_file = os.path.join(root,tdms_file)
                this_hash = hashfile(this_file)
                if this_hash == tdms_hash:
                    return this_file


def crop_linear_data(data, xmin, xmax, ymin, ymax):
    """ Crop plotting data.
    
    Crops plotting data of monotonous function and linearly interpolates
    values at end of interval.
    
    Paramters
    ---------
    data : ndarray of shape (N,2)
        The data to be filtered in x and y.
    xmin : float
        minimum value for data[:,0]
    xmax : float
        maximum value for data[:,0]
    ymin : float
        minimum value for data[:,1]
    ymax : float
        maximum value for data[:,1]    
    
    
    Returns
    -------
    ndarray of shape (M,2), M<=N
    
    Notes
    -----
    `data` must be monotonically increasing in x and y.
    
    """
    # TODO:
    # Detect re-entering of curves into plotting area
    x = data[:,0].copy()
    y = data[:,1].copy()
    
    # Filter xmin
    if np.sum(x<xmin) > 0:
        idxmin = np.sum(x<xmin)-1
        xnew = x[idxmin:].copy()
        ynew = y[idxmin:].copy()
        xnew[0] = xmin
        ynew[0] = np.interp(xmin, x, y)
        x = xnew
        y = ynew


    # Filter ymax
    if np.sum(y>ymax) > 0:
        idymax = len(y)-np.sum(y>ymax)+1
        xnew = x[:idymax].copy()
        ynew = y[:idymax].copy()
        ynew[-1] = ymax
        xnew[-1] = np.interp(ymax, y, x)
        x = xnew
        y = ynew
        

    # Filter xmax
    if np.sum(x>xmax) > 0:
        idxmax = len(y)-np.sum(x>xmax)+1
        xnew = x[:idxmax].copy()
        ynew = y[:idxmax].copy()
        xnew[-1] = xmax
        ynew[-1] = np.interp(xmax, x, y)
        x = xnew
        y = ynew
        
    # Filter ymin
    if np.sum(y<ymin) > 0:
        idymin = np.sum(y<ymin)-1
        xnew = x[idymin:].copy()
        ynew = y[idymin:].copy()
        ynew[0] = ymin
        xnew[0] = np.interp(ymin, y, x)
        x = xnew
        y = ynew
    
    newdata = np.zeros((len(x),2))
    newdata[:,0] = x
    newdata[:,1] = y

    return newdata





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
                # Ignore broken measurements
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
            dn = u"{} {}".format(mx, GetRegion(f))
            if not GetRegion(f).lower() in ["reservoir"]:
                # outlet (flow rate is not important)
                dn += u"  {} µls⁻¹".format(GetFlowRate(f))
            dn += "  ({} events)".format(GetEvents(f))
                                   
            treelist[i].append((dn, f))
        
    return treelist, cols


def IsFullMeasurement(fname):
    """ Checks for existence of ini files and returns False if some
        files are missing.
    """
    is_ok = True
    path, name = os.path.split(fname)
    mx = name.split("_")[0]
    stem = os.path.join(path, mx)
    
    # Check if all config files are present
    if ( (not os.path.exists(stem+"_para.ini")) or
         (not os.path.exists(stem+"_camera.ini")) or
         (not os.path.exists(fname))                ):
        is_ok = False
    
    # Check if we can perform all standard file operations
    for test in [GetRegion, GetFlowRate, GetEvents]:
        try:
            test(fname)
        except:
            is_ok = False
            break
    
    return is_ok


def GetDefaultConfiguration(key=None):
    config = dfn.LoadDefaultConfiguration()
    config = dfn.LoadConfiguration(cfg_file, config)
    if key is not None:
        return config[key]
    else:
        return config


def GetEvents(fname):
    """ Get the number of events for a tdms file
    """
    tdms_file = TdmsFile(fname)
    datalen = len(tdms_file.object("Cell Track", "time").data)
    return datalen


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
    with codecs.open(cfgfilename, 'r', "utf-8") as f:
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
