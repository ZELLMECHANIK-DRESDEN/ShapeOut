#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - Analysis class"""
from __future__ import division, unicode_literals

import chaco.api as ca
from chaco.color_mapper import ColorMapper
import codecs
import copy
import numpy as np
import os
import warnings

# dclab imports
import dclab
from dclab.rtdc_dataset import RTDC_DataSet, Configuration, fmt_tdms,\
    fmt_hierarchy
from dclab.polygon_filter import PolygonFilter
import dclab.definitions as dfn

from .tlabwrap import IGNORE_AXES
from shapeout import tlabwrap
from .gui import session


class Analysis(object):
    """ An object that stores several RTDC data sets and useful methods
    
    This object contains
     - RTDC data sets
     - common configuration parameters of the data sets
     - Plotting parameters
    """
    def __init__(self, data, search_path="./", config={}):
        """ Analysis data object.
        
        Parameters
        ----------
        data: str or list of (str, dclab.RTDC_DataSet)
            The data to load. The nature of `data` is inferred
            from its type:
            - str: A session 'index.txt' file
            - list: A list of paths of tdms files or RTDC_DataSet
        search_path: str
            In case `data` is a string, `search_path` is used to
            find missing tdms files on disk.
        config: dict
            A configuration dictionary that will be applied to
            each RTDC_DataSet before completing the configuration
            and data. The completion of the configuration takes
            place at the end of the initialization of this class and
            the configuration must be applied beforehand to make
            sure that parameters such as "emodulus" are computed.
        """
        self.measurements = []
        if isinstance(data, list):
            # New analysis
            for f in data:
                if os.path.exists(unicode(f)):
                    rtdc_ds = RTDC_DataSet(tdms_path=f)
                else:
                    # RTDC data set
                    rtdc_ds = f
                self.measurements.append(rtdc_ds)
        elif isinstance(data, (unicode, str)) and os.path.exists(data):
            # We are opening a session "index.txt" file
            self._ImportDumped(data, search_path=search_path)
        else:
            raise ValueError("Argument not an index file or list of"+\
                             " .tdms files: {}".format(data))
        # Set configuration (e.g. from previous analysis)
        if config:
            self.SetParameters(config)
        # Complete missing configuration parameters
        self._complete_config()
        # Reset contour accuracies
        self.init_plot_accuracies()


    def _clear(self):
        """Remove all attributes from this instance, making it unusable
        
        It is difficult to control how the chaco plots refer to a measurement
        object.
        
        """
        import gc
        for _i in range(len(self.measurements)):
            mm = self.measurements.pop(0)
            # Deleting all the data in measurements!
            attrs = copy.copy(dclab.definitions.rdv)
            attrs += ["_filter_"+a for a in attrs]
            attrs += ["_filter"]
            for a in attrs:
                if hasattr(mm, a):
                    b = mm[a]
                    del b
            refs = gc.get_referrers(mm)
            for r in refs:
                if hasattr(r, "delplot"):
                    r.delplot()
                del r
            del mm
        gc.collect()


    def _complete_config(self, measurements=None):
        """Complete configuration of all RTDC_DataSet sets
        
        Sets configuration keywords that are not (necessarily)
        used/required by dclab.
        """
        if measurements is None:
            measurements = self.measurements
        
        for mm in measurements:
            # Update configuration with default values from ShapeOut,
            # but do not override anything.
            cfgold = mm.config.copy()
            mm.config.update(tlabwrap.cfg)
            mm.config.update(cfgold)
            ## Sensible values for default contour accuracies
            keys = []
            for prop in self.GetPlotAxes():
                if dfn.cfgmaprev[prop] in mm:
                    # There are values for this uid
                    keys.append(dfn.cfgmaprev[prop])
            # This lambda function seems to do a good job
            accl = lambda a: (remove_nan_inf(a).max()-remove_nan_inf(a).min())/10
            defs = [["contour accuracy {}", accl],
                    ["kde accuracy {}", accl],
                   ]
            pltng = mm.config["plotting"]
            for kk in keys:
                for d, l in defs:
                    var = d.format(dfn.cfgmap[kk])
                    if var not in pltng:
                        pltng[var] = l(mm[kk])
            ## Check for missing min/max values and set them to zero
            for item in dfn.uid:
                appends = [" min", " max"]
                for a in appends:
                    if not item+a in mm.config["plotting"]:
                        mm.config["plotting"][item+a] = 0


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
        datadict = session.index_load(indexname)
        keys = list(datadict.keys())
        # The identifier (in brackets []) contains a number before the first
        # underscore "_" which determines the order of the plots:
        #keys.sort(key=lambda x: int(x.split("_")[0]))
        measmts = [None]*len(keys)
        while measmts.count(None):
            for key in keys:
                kidx = int(key.split("_")[0])-1
                if measmts[kidx] is not None:
                    # we have already imported that measurement
                    continue
                
                data = datadict[key]
                # os.path.normpath replaces forward slash with
                # backslash on Windows
                config_file = os.path.normpath(os.path.join(thedir,
                                                            data["config"]))
                cfg = Configuration(files=[config_file])
                
                # backwards compatibility:
                # - 0.7.1: replace "kde multivariate" with "kde accuracy"
                for kk in list(cfg["plotting"].keys()):
                    if kk.startswith("kde multivariate "):
                        ax = kk.split()[2]
                        cfg["plotting"]["kde accuracy "+ax] = cfg["plotting"][kk]
                        cfg["plotting"].pop(kk)
                # - 0.7.5: remove unused computation of emodulus from config
                if "kde accuracy emodulus" not in cfg["plotting"]:
                    # user did not compute emodulus
                    if "calculation" in cfg:
                        for kk in ["emodulus medium", 
                                   "emodulus model",
                                   "emodulus temperature",
                                   "emodulus viscosity"]:
                            if kk in cfg["calculation"]:
                                cfg["calculation"].pop(kk)
                # Start importing data
                if ("special type" in data and
                    data["special type"] == "hierarchy child"):
                    # Check if the parent exists
                    idhp = cfg["Filtering"]["Hierarchy Parent"]
                    ids = [mm.identifier for mm in measmts if mm is not None]
                    mms = [mm for mm in measmts if mm is not None]
                    if idhp in ids:
                        # parent exists
                        hparent = mms[ids.index(idhp)]  
                        mm = RTDC_DataSet(hparent=hparent)
                    else:
                        # parent doesn't exist - try again in next loop
                        continue
                else:
                    tloc = session.get_tdms_file(data, search_path)
                    mm = RTDC_DataSet(tloc)
                    mmhashes = [h[1] for h in mm.file_hashes]
                    newhashes = [ data["tdms hash"], data["camera.ini hash"],
                                  data["para.ini hash"]
                                ]
                    if mmhashes != newhashes:
                        msg = "File hashes don't match for: {}".format(tloc)
                        warnings.warn(msg, HashComparisonWarning)


                if "title" in data:
                    # title saved starting version 0.5.6.dev6
                    mm.title = data["title"]
                
                # Load manually excluded events
                filter_manual_file = os.path.join(os.path.dirname(config_file),
                                                  "_filter_manual.npy")
                
                if os.path.exists(filter_manual_file):
                    mm._filter_manual = np.load(os.path.join(filter_manual_file))
                
                mm.config.update(cfg)
                mm.ApplyFilter()
                measmts[kidx] = mm

        self.measurements = measmts


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
            has_tdms = isinstance(mm, fmt_tdms.RTDC_TDMS)
            is_hchild = isinstance(mm, fmt_hierarchy.RTDC_Hierarchy)
            amsg = "RTDC_DataSet must be from tdms file or hierarchy child!"
            assert has_tdms+is_hchild, amsg
            i += 1
            ident = "{}_{}".format(i, mm.name)
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
            if has_tdms:
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
            elif is_hchild:
                out.append("special type = hierarchy child")
            out.append("title = "+mm.title)
            # Save configurations
            cfgfile = os.path.join(mmdir, "config.txt")
            mm.config.save(cfgfile)
            # Use forward slash such that sessions saved on Windows
            # can be opened on *nix as well.
            out.append("config = {}/config.txt".format(ident))
            
            # save manual filters
            np.save(os.path.join(mmdir, "_filter_manual.npy"), mm._filter_manual)
            
            if fullout:
                # create directory that contains tdms and ini files
                
                ## create copy function that works on all oses!
                raise NotImplementedError("Unable to copy files!")

            out.append("")
            
        for i in range(len(out)):
            out[i] += "\r\n"
        
        with codecs.open(indexname, "w", "utf-8") as index:
            index.writelines(out)
        
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
        cfgreset = {"filtering":{"limit events":0}}
        # This also calls ApplyFilter and comutes clean filters
        self.SetParameters(cfgreset)
        
        # Get minimum size
        minsize = np.inf
        for m in self.measurements:
            minsize = min(minsize, np.sum(m._filter))
            print(minsize)
        cfgnew = {"filtering":{"limit events":minsize}}
        self.SetParameters(cfgnew)
        return minsize


    def GetCommonParameters(self, key):
        """
        For as key (e.g. "Filtering") find all parameters that are given
        for every measurement in the analysis.
        """
        retdict = dict()
        if key in self.measurements[0].config:
            s = set(self.measurements[0].config[key].items())
            for m in self.measurements[1:]:
                s2 = set(m.config[key].items())
                s = s & s2
            for item in s:
                retdict[item[0]] = item[1]
        return retdict


    def GetContourColors(self):
        colors = list()
        for mm in self.measurements:
            colors.append(mm.config["Plotting"]["Contour Color"])
        return colors


    def GetNames(self):
        """ Returns the names of all measurements """
        names = list()
        for mm in self.measurements:
            names.append(mm.name)
        return names


    def GetPlotAxes(self, mid=0):
        p = self.GetParameters("plotting", mid)
        return [p["axis x"].lower(), p["axis y"].lower()]


    def GetPlotGeometry(self, mid=0):
        p = self.GetParameters("Plotting", mid)
        return (int(p["Rows"]), int(p["Columns"]),
                int(p["Contour Plot"]), int(p["Legend Plot"]))


    def GetStatisticsBasic(self):
        """
        Computes Mean, Avg, etc for all data sets and returns two lists:
        The headings and the values.
        """
        datalist = []
        head = None
        for mm in self.measurements:
            axes= [mm.config["plotting"]["axis x"].lower(),
                   mm.config["plotting"]["axis y"].lower()]
            h, v = dclab.statistics.get_statistics(mm, axes=axes)
            # Make sure all columns are equal
            if head is not None:
                assert head == h, "'{}' has wrong columns!".format(mm.title)
            else:
                head = h
            datalist.append([mm.title]+v)
            
        head = ["Data set"] + head
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
        if key in self.measurements[0].config:
            s = set(self.measurements[0].config[key].items())
            uncom = set(com.items()) ^ s
            for m in self.measurements[1:]:
                s2 = set(m.config[key].items())
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
                    if m.config[key].has_key(item[0]):
                        vals.append(m.config[key][item[0]])
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
                if atname not in mm:
                    unusable.append(ax.lower())
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
        conf = self.measurements[mid].config.copy()[key]
        unusable_axes = self.GetUnusableAxes()
        pops = []
        for k in conf:
            # remove generally ignored items from config
            for ax in IGNORE_AXES:
                if k.startswith(ax) or k.endswith(ax):
                    pops.append(k)
            # remove axes that are not owned by all measurements
            if k.endswith("max"):
                ax = k[:-4]
                if ax in unusable_axes:
                    pops.append(k)
        for k in list(set(pops)):
            conf.pop(k)
            
        return conf


    def init_plot_accuracies(self):
        """ Set initial (heuristic) accuracies for all plots.
        
        It is not always easy to determine the correct accuracy for
        the contour plots. This method sets these accuracies for the user.
        
        All keys of the active axes are changed, e.g.:
          - "contour accuracy area"
          - "contour accuracy defo"
          - "kde accuracy defo"
          - "kde accuracy defo"
        
        Note that the accuracies are not updated when the key
        ["Plotting"]["Contour Fix Scale"] is set to `True` for the
        first measurement of the analysis.
        """
        # check if updating is disabled:
        if self.measurements[0].config["plotting"]["contour fix scale"]:
            return
        
        # Remove contour accuracies for the current plots
        for key in dfn.uid:
            for mm in self.measurements:
                for var in ["contour accuracy {}".format(key),
                            "kde accuracy {}".format(key)]:
                    if var in mm.config["plotting"]:
                        mm.config["plotting"].pop(var)

        # Set default accuracies
        self._complete_config()


    def PolygonFilterRemove(self, filt):
        """
        Removes a polygon filter from all elements of the analysis.
        """
        for mm in self.measurements:
            try:
                mm.polygon_filter_rm(filt)
            except ValueError:
                pass


    def SetContourColors(self, colors=None):
        """ Sets the contour colors.
        
        If colors is given and if it the number of colors is equal or
        greater than the number of measurements, then the colors are
        applied to the measurement. Otherwise, default colors are used.
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

            for ii, mm in enumerate(self.measurements):
                mm.config["plotting"]["contour color"] = colors[ii]


    def SetParameters(self, newcfg):
        """ updates the RTDC_DataSet configuration

        """
        upcfg = {}
        if "filtering" in newcfg:
            upcfg["filtering"] = newcfg["filtering"].copy()
        if "plotting" in newcfg:
            upcfg["plotting"] = newcfg["plotting"].copy()
            # prevent applying indivual things to all measurements
            ignorelist = ["contour color"]
            pops = []
            for skey in upcfg["plotting"]:
                if skey in ignorelist:
                    pops.append(skey)
            for skey in pops:
                upcfg["plotting"].pop(skey)
            # Address issue with faulty contour plot on log scale
            # https://github.com/enthought/chaco/issues/300
            pl = upcfg["plotting"]
            if (("scale x" in pl and pl["scale x"] == "log") or
                ("scale y" in pl and pl["scale y"] == "log")):
                warnings.warn("Disabling contour plot because of chaco issue #300!")
                upcfg["plotting"]["contour plot"] = False
        if "analysis" in newcfg:
            upcfg["analysis"] = newcfg["analysis"].copy()
            ignorelist = ["regression treatment", "regression repetition"]
            pops = []
            for skey in upcfg["analysis"]:
                if skey in ignorelist:
                    pops.append(skey)
            for skey in pops:
                upcfg["analysis"].pop(skey)
        if "calculation" in newcfg:
            upcfg["calculation"] = newcfg["calculation"].copy()

        for mm in self.measurements:
            # update configuration
            mm.config.update(upcfg)
        for mm in self.measurements:
            # apply filter in separate loop (safer for hierarchies)
            mm.ApplyFilter()
        
        # Trigger computation of kde/contour accuracies for ancillary columns
        self._complete_config()


class HashComparisonWarning(UserWarning):
    pass


def darkjet(myrange, **traits):
    """ Generator function for the 'darkjet' colormap. """
    _data = {'red': ((0., 0, 0), (0.35, 0.0, 0.0), (0.66, .3, .3), (0.89, .4, .4),
    (1, 0.5, 0.5)),
    'green': ((0., 0.0, 0.0), (0.125, .1, .10), (0.375, .4, .4), (0.64,.3, .3),
    (0.91,0.2,0.2), (1, 0, 0)),
    'blue': ((0., 0.7, 0.7), (0.11, .5, .5), (0.34, .4, .4), (0.65, 0, 0),
    (1, 0, 0))}
    return ColorMapper.from_segment_map(_data, range=myrange, **traits)


def remove_nan_inf(x):
    for issome in [np.isnan, np.isinf]:
        xsome = issome(x)
        x = x[~xsome]
    return x
