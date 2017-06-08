#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - more functionalities for dclab

"""
from __future__ import division, unicode_literals

import codecs
import copy
import cv2
from distutils.version import LooseVersion

import numpy as np
from nptdms import TdmsFile
import os
import warnings

import dclab
from dclab.rtdc_dataset.fmt_tdms import get_project_name_from_path, get_tdms_files
from dclab.rtdc_dataset import config as rt_config
from util import findfile


# Constants in OpenCV moved from "cv2.cv" to "cv2"
if LooseVersion(cv2.__version__) < LooseVersion("3.0.0"):
    cv_const = cv2.cv
    cv_version3 = False
else:
    cv_const = cv2
    cv_version3 = True


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
        files = get_tdms_files(directory)

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
                treelist.append([])
                i = len(treelist)-1
                pathdict[path] = i
                # The first element of a tree contains the measurement name
                project = get_project_name_from_path(path)
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


def get_config_entry_choices(key, subkey, ignore_axes=[]):
    """ Returns the choices for a parameter, if any
    """
    key = key.lower()
    subkey = subkey.lower()
    ignore_axes = [a.lower() for a in ignore_axes]
    ## Manually defined types:
    choices = []
    
    if key == "plotting":
        if subkey == "kde":
            choices = list(dclab.kde_methods.methods.keys())
        elif subkey in ["axis x", "axis y"]:
            choices = copy.copy(dclab.dfn.uid)
            # remove unwanted axes
            for choice in ignore_axes:
                if choice in choices:
                    choices.remove(choice)
        elif subkey in ["rows", "columns"]:
            choices = [ str(i) for i in range(1,6) ]
        elif subkey in ["scatter marker size"]:
            choices = [ str(i) for i in range(1,5) ]
        elif subkey.count("scale "):
            choices = ["linear", "log"]
    elif key == "analysis":
        if subkey == "regression model":
            choices = ["lmm", "glmm"]
    elif key == "calculation":
        if subkey == "emodulus model":
            choices = ["elastic sphere"]
        if subkey == "emodulus medium":
            choices = ["CellCarrier", "CellCarrier B", "Other"]
    return choices


def get_config_entry_dtype(key, subkey, refcfg=None):
    """ Returns dtype of the parameter as defined in dclab.cfg
    """
    key = key.lower()
    subkey = subkey.lower()
    #default
    dtype = str

    ## Define dtypes and choices of cfg content
    # Iterate through cfg to determine standard dtypes
    cfg_init = cfg.copy()  
    if refcfg is None:
        refcfg = cfg_init.copy()
   
    if key in cfg_init and subkey in cfg_init[key]:
        dtype = cfg_init[key][subkey].__class__
    else:
        try:
            dtype = refcfg[key][subkey].__class__
        except KeyError:
            dtype = float

    return dtype


def GetDefaultConfiguration(key=None):
    cfg = rt_config.load_from_file(cfg_file)
    if key is not None:
        return cfg[key]
    else:
        return cfg


def GetEvents(fname):
    """ Get the number of events for a tdms file
    
    There are multiple ways of determining the number of events,
    which are used in the following order:
    1. The MX_log.ini file "Events" tag
    2. The number of frames in the avi file
    3. The tdms file (very slow, because whole tdms file is loaded)
    
    """
    mdir = os.path.dirname(fname)
    mid = os.path.basename(fname).split("_")[0]
    # 1. The MX_log.ini file "Events" tag
    logf = os.path.join(mdir, mid+"_log.ini")
    # 2. The number of frames in the avi file
    avif = os.path.join(mdir, mid+"_imaq.avi")
    if os.path.exists(logf):
        with open(logf) as fd:
            logd = fd.readlines()
        for l in logd:
            if l.strip().startswith("Events:"):
                datalen = int(l.split(":")[1])
                break
    elif os.path.exists(avif):
        video = cv2.VideoCapture(avif)
        if cv_version3:
            datalen = video.get(cv_const.CAP_PROP_FRAME_COUNT)
        else:
            datalen = video.get(cv_const.CV_CAP_PROP_FRAME_COUNT)
        video.release()
    else:
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
        camcfg = rt_config.load_from_file(stem+"_para.ini")
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
        camcfg = rt_config.load_from_file(stem+"_para.ini")
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
            Plot1 = "defo area"
            Plot2 = "circ area"
            Plot3 = "area defo"
            Plot4 = "area circ"
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
cfg = rt_config.load_from_file(cfg_file)
cfg_ordered_list = GetConfigurationKeys(cfg_file)

thispath = os.path.dirname(os.path.realpath(__file__))
isoeldir = findfile("isoelastics")
isoelastics = LoadIsoelastics(os.path.join(thispath, isoeldir))

# Axes that should not be displayed  by Shape Out
IGNORE_AXES = ["areapix", "frame", "arearaw"]
