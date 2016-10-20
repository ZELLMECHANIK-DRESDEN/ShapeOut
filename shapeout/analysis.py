#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - Analysis class

"""
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
from dclab.rtdc_dataset import RTDC_DataSet
from dclab.polygon_filter import PolygonFilter
import dclab.definitions as dfn
from dclab import config

from .tlabwrap import IGNORE_AXES



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
        datadict = config.load_config_file(indexname, capitalize=False)
        keys = list(datadict.keys())
        # The identifier (in brackets []) contains a number before the first
        # underscore "_" which determines the order of the plots:
        #keys.sort(key=lambda x: int(x.split("_")[0]))
        measmts = [None]*len(keys)
        while measmts.count(None):
            for key in keys:
                kidx = int(key[0])-1
                if measmts[kidx] is not None:
                    # we have already imported that measurement
                    continue
                
                data = datadict[key]
                config_file = os.path.join(thedir, data["config"])
                cfg = config.load_config_file(config_file)
                
                if ("special type" in data and
                    data["special type"] == "hierarchy child"):
                    # Check if the parent exists
                    idhp = cfg["Filtering"]["Hierarchy Parent"]
                    ids = [mm.identifier for mm in measmts if mm is not None]
                    mms = [mm for mm in measmts if mm is not None]
                    if idhp in ids:
                        hparent = mms[ids.index(idhp)]  
                        mm = RTDC_DataSet(hparent=hparent)
                else:
                    tloc = session_get_tdms_file(data, search_path)
                    mm = RTDC_DataSet(tloc)
                    mmhashes = [h[1] for h in mm.file_hashes]
                    newhashes = [ data["tdms hash"], data["camera.ini hash"],
                                  data["para.ini hash"]
                                ]
                    if mmhashes != newhashes:
                        raise ValueError("Hashes don't match for file {}.".
                                         format(tloc))
                if "title" in data:
                    # title saved starting version 0.5.6.dev6
                    mm.title = data["title"]
                
                # Load manually excluded events
                filter_manual_file = os.path.join(os.path.dirname(config_file),
                                                  "_filter_manual.npy")
                if os.path.exists(filter_manual_file):
                    mm._filter_manual = np.load(os.path.join(filter_manual_file))
                
                mm.UpdateConfiguration(cfg)
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
            has_tdms = os.path.exists(mm.tdms_filename)
            is_hchild = hasattr(mm, "hparent")
            amsg = "RTDC_DataSet must be from tdms file or hierarchy child!"
            assert has_tdms+is_hchild, amsg
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
            config.save_config_file(cfgfile, mm.Configuration)
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
        datalist = []
        head = None
        for mm in self.measurements:
            axes = mm.GetPlotAxes()
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



def darkjet(myrange, **traits):
    """ Generator function for the 'darkjet' colormap. """
    _data = {'red': ((0., 0, 0), (0.35, 0.0, 0.0), (0.66, .3, .3), (0.89, .4, .4),
    (1, 0.5, 0.5)),
    'green': ((0., 0.0, 0.0), (0.125, .1, .10), (0.375, .4, .4), (0.64,.3, .3),
    (0.91,0.2,0.2), (1, 0, 0)),
    'blue': ((0., 0.7, 0.7), (0.11, .5, .5), (0.34, .4, .4), (0.65, 0, 0),
    (1, 0, 0))}
    return ColorMapper.from_segment_map(_data, range=myrange, **traits)


def session_check_index(indexname, search_path="./"):
    """ Check a session file index for existance of all measurement files
    """
    missing_files = []
    
    datadict = config.load_config_file(indexname, capitalize=False)
    keys = list(datadict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    keys.sort(key=lambda x: int(x.split("_")[0]))
    for key in keys:    
        data = datadict[key]
        if not ("special type" in data and
                data["special type"] == "hierarchy child"):
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
    datadict = config.load_config_file(indexname, capitalize=False)
    for key in updict:
        datadict[key].update(updict[key])
    config.save_config_file(indexname, datadict)