#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - configuration parameters relevant for the GUI"""
from __future__ import division, unicode_literals

import copy
import io
import os
import pkg_resources

import dclab
from dclab.rtdc_dataset import config as rt_config


def get_config_entry_choices(key, subkey, ignore_axes=[]):
    """Return the choices for a parameter, if any"""
    key = key.lower()
    subkey = subkey.lower()
    ignore_axes = [a.lower() for a in ignore_axes]
    ## Manually defined types:
    choices = []
    
    if key == "plotting":
        if subkey == "kde":
            choices = list(dclab.kde_methods.methods.keys())
        elif subkey in ["axis x", "axis y"]:
            choices = copy.copy(dclab.dfn.scalar_feature_names)
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
        elif subkey == "isoelastics":
            choices = ["not shown", "analytical", "numerical", "legacy"]
        elif subkey == "contour level mode":
            choices = ["fraction", "quantile"]
    elif key == "analysis":
        if subkey == "regression model":
            choices = ["lmm", "glmm"]
    elif key == "calculation":
        if subkey == "emodulus model":
            choices = ["elastic sphere"]
        if subkey == "emodulus medium":
            choices = ["CellCarrier", "CellCarrier B", "water", "Other"]
    return choices


def get_config_entry_dtype(key, subkey, refcfg=None):
    """Return dtype of the parameter as defined in dclab.cfg"""
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


def GetConfigurationKeys(cfgfilename, capitalize=True):
    """
    Load the configuration file and return the list of variables
    in the order they appear.
    """
    with io.open(cfgfilename, 'r') as f:
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
    Sort a list of configuration keys according to the appearance in the
    Shape-Out default.cfg configuration file.
    
    If items are not present in this file, then the will be sorted according to
    the string value.
    
    This function is used to determine the displayed order of parameters in
    Shape-Out using the configuration file `default.cfg`.
    
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

cfg_dir = pkg_resources.resource_filename("shapeout", "cfg")
cfg_file = os.path.join(cfg_dir, "default.cfg")
cfg = rt_config.load_from_file(cfg_file)
cfg_ordered_list = GetConfigurationKeys(cfg_file)
