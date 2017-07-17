#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - Analysis class"""
from __future__ import division, unicode_literals

import chaco.api as ca
from chaco.color_mapper import ColorMapper
import gc
import io
import numpy as np
import os
import warnings

# dclab imports
import dclab
from dclab.rtdc_dataset import Configuration
from dclab.polygon_filter import PolygonFilter
import dclab.definitions as dfn

from .tlabwrap import IGNORE_AXES
from shapeout import tlabwrap
from ._version import version
from . import session

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
        data: str or list of (str, dclab.rtdc_dataset.RTDCBase)
            The data to load. The nature of `data` is inferred
            from its type:
            - str: A session 'index.txt' file
            - list: A list of paths of measurement files or instances
                    of RTDCBase
        search_path: str
            In case `data` is a string, `search_path` is used to
            find missing files on disk.
        config: dict
            A configuration dictionary that will be applied to
            each RT-DC dataset before completing the configuration
            and data. The completion of the configuration takes
            place at the end of the initialization of this class and
            the configuration must be applied beforehand to make
            sure that parameters such as "emodulus" are computed.
        """
        # Start importing measurements
        self.measurements = []
        if isinstance(data, list):
            # New analysis
            for f in data:
                if os.path.exists(unicode(f)):
                    rtdc_ds = dclab.new_dataset(f)
                else:
                    # RTDC data set
                    rtdc_ds = f
                self.measurements.append(rtdc_ds)
        elif isinstance(data, (unicode, str)) and os.path.exists(data):
            # We are opening a session "index.txt" file
            self._ImportDumped(data, search_path=search_path)
        else:
            raise ValueError("Argument not an index file or list of"+\
                             " measurement files: {}".format(data))
        
        # Set configuration (e.g. from previous analysis)
        if config:
            self.SetParameters(config)
        # Complete missing configuration parameters
        self._complete_config()
        

    def _clear(self):
        """Remove all attributes from this instance, making it unusable
        
        It is difficult to control how the chaco plots refer to a measurement
        object.
        
        """
        for _i in range(len(self.measurements)):
            mm = self.measurements.pop(0)
            # Deleting all the data in measurements!
            refs = gc.get_referrers(mm)
            for r in refs:
                if hasattr(r, "delplot"):
                    r.delplot()
                del r
            del mm
        # Reset contour accuracies
        self.reset_plot_accuracies()
        gc.collect()


    def _complete_config(self, measurements=None):
        """Complete configuration of all RT-DC datasets
        
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
            # This lambda function seems to do a good job
            accl = lambda a: (remove_nan_inf(a).max()-remove_nan_inf(a).min())/10
            defs = [["contour accuracy {}", accl],
                    ["kde accuracy {}", accl],
                   ]
            pltng = mm.config["plotting"]
            for kk in self.GetPlotAxes():
                for d, l in defs:
                    var = d.format(kk)
                    if var not in pltng:
                        pltng[var] = l(mm[kk])
            ## Check for missing min/max values and set them to zero
            for item in dfn.column_names:
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
            Relative search path where to look for measurement files if
            the absolute path stored in index.txt cannot be found.
        """
        ## Read index file and locate measurement file.
        thedir = os.path.dirname(indexname)
        # Load polygons before importing any data
        polygonfile = os.path.join(thedir, "PolygonFilters.poly")
        PolygonFilter.clear_all_filters()
        if os.path.exists(polygonfile):
            PolygonFilter.import_all(polygonfile)
        # import configurations
        index_dict = session.index.index_load(indexname)
        keys = list(index_dict.keys())
        # The identifier (in brackets []) contains a number before the first
        # underscore "_" which determines the order of the plots:
        #keys.sort(key=lambda x: int(x.split("_")[0]))
        measmts = [None]*len(keys)
        while measmts.count(None):
            for key in keys:
                # The order in keys is not important to correctly reproduce
                # a session. Important is the integer number before the
                # underscore.
                kidx = int(key.split("_")[0])-1
                if measmts[kidx] is not None:
                    # we have already imported that measurement
                    continue
                
                item = index_dict[key]
                # os.path.normpath replaces forward slash with
                # backslash on Windows
                config_file = os.path.normpath(os.path.join(thedir,
                                                            item["config"]))
                cfg = Configuration(files=[config_file])

                # Start importing data
                if ("special type" in item and
                    item["special type"] == "hierarchy child"):
                    # check if parent is already here
                    pidx = int(item["parent id"].split("_")[0])-1
                    hparent = measmts[pidx]
                    if hparent is not None:
                        mm = dclab.new_dataset(hparent)
                    else:
                        # parent doesn't exist - try again in next loop
                        continue
                else:
                    tloc = session.index.find_data_path(item, search_path)
                    mm = dclab.new_dataset(tloc)
                    if mm.hash != item["hash"]:
                        msg = "File hashes don't match for: {}".format(tloc)
                        warnings.warn(msg, HashComparisonWarning)

                if "title" in item:
                    # title saved starting version 0.5.6.dev6
                    mm.title = item["title"]
                
                # Load manually excluded events
                filter_manual_file = os.path.join(os.path.dirname(config_file),
                                                  "_filter_manual.npy")
                
                if os.path.exists(filter_manual_file):
                    mm.filter.manual[:] = np.load(os.path.join(filter_manual_file))

                mm.config.update(cfg)
                mm.apply_filter()
                measmts[kidx] = mm
        self.measurements = measmts


    def DumpData(self, directory, rel_path="./"):
        """ Dumps all the data from the analysis to a `directory`
        
        Returns a list of filenames that are required to restore this
        analysis. The "index.txt" contains the relative paths to all
        configuration files.
        """
        indexname = os.path.join(directory, "index.txt")
        # Create Index file
        out = ["# ShapeOut measurement index",
               "# Software version {}".format(version)]
        
        i = 0
        for mm in self.measurements:
            amsg = "RT-DC dataset must be from tdms file or hierarchy child!"
            assert mm.format in ["tdms", "hierarchy"], amsg
            i += 1
            ident = "{}_{}".format(i, mm.identifier)
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
            out.append("title = "+mm.title)            
            out.append("hash = {}".format(mm.hash))
            if mm.format in ["tdms", "hdf5"]:
                out.append("name = {}".format(os.path.basename(mm.path)))
                out.append("fdir = {}".format(os.path.dirname(mm.path)))
                try:
                    # On Windows we have multiple drive letters and
                    # relpath will complain about that if dirname(mm.path)
                    # and rel_path are not on the same drive.
                    rdir = os.path.relpath(os.path.dirname(mm.path), rel_path)
                except ValueError:
                    rdir = "."
                out.append("rdir = {}".format(rdir))
                # save manual filters only for real data
                # (see https://github.com/ZELLMECHANIK-DRESDEN/dclab/issues/22)
                np.save(os.path.join(mmdir, "_filter_manual.npy"), mm.filter.manual)
            elif mm.format == "hierarchy":
                pidx = self.measurements.index(mm.hparent) + 1
                p_ident = "{}_{}".format(pidx, mm.hparent.identifier)
                out.append("special type = hierarchy child")
                out.append("parent hash = {}".format(mm.hparent.hash))
                out.append("parent id = {}".format(p_ident))
            # Save configurations
            cfgfile = os.path.join(mmdir, "config.txt")
            mm.config.save(cfgfile)
            # Use forward slash such that sessions saved on Windows
            # can be opened on *nix as well.
            out.append("config = {}/config.txt".format(ident))
            out.append("")
            
        for i in range(len(out)):
            out[i] += "\n"
        
        with io.open(indexname, "w") as index:
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
        # This also calls apply_filter and comutes clean filters
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
        """ Returns the titles of all measurements """
        names = list()
        for mm in self.measurements:
            names.append(mm.title)
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


    def GetFilenames(self):
        """Returns paths of measurements"""
        names = list()
        for mm in self.measurements:
            names.append(mm.path)
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
            for nn in self.measurements[1:]:
                s2 = set(nn.config[key].items())
                uncom2 = set(com.items()) ^ s2
                
                newuncom = dict()
                uncom.symmetric_difference_update(uncom2)
                for _i in range(len(uncom)):
                    item = uncom.pop()
                    newuncom[item[0]] = None
                uncom = set(newuncom.items())
                    
            for item in uncom:
                vals = list()
                for mm in self.measurements:
                    if mm.config[key].has_key(item[0]):
                        vals.append(mm.config[key][item[0]])
                    else:
                        vals.append(None)
                        warnings.warn(
                          "Measurement {} might be corrupt!".format(mm.title))
                retdict[item[0]] = vals
        return retdict        


    def GetUnusableAxes(self):
        """ 
        Unusable axes are axes that are not shared by all measurements
        or that are ignored by default.

        See Also
        --------
        GetUsableAxes
        """
        unusable = []
        for ax in dfn.column_names:
            if ax in IGNORE_AXES:
                unusable.append(ax)
                continue
            for mm in self.measurements:
                # Get the attribute name for the axis
                if ax not in mm:
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
        for ax in dfn.column_names:
            if not ax in unusable:
                usable.append(ax)
        return usable


    def GetParameters(self, key, mid=0, filter_for_humans=True):
        """Get parameters that all measurements share."""
        conf = self.measurements[mid].config.copy()[key]
        unusable_axes = self.GetUnusableAxes()
        pops = []
        for k in conf:
            # remove axes that are not owned by all measurements
            if k.endswith(" max"):
                ax = k[:-4]
                if ax in unusable_axes:
                    pops.append("kde accuracy {}".format(ax))
                    pops.append("contour accuracy {}".format(ax))
                    pops.append("{} min".format(ax))
                    pops.append("{} max".format(ax))
        for k in list(set(pops)):
            if k in conf:
                conf.pop(k)
            
        return conf


    def reset_plot_accuracies(self):
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
        if (len(self.measurements) == 0 or
            self.measurements[0].config["plotting"]["contour fix scale"]):
            return
        
        # Remove contour accuracies for the current plots
        for key in dfn.column_names:
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
        """ updates the RT-DC dataset configuration

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
            mm.apply_filter()
        
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
