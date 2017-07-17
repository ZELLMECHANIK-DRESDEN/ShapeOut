#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration file handling for ShapeOut"""
from __future__ import division, print_function, unicode_literals

import io
import os
from os.path import join

import appdirs

CFGNAME = "shapeout.cfg"
DEFAULTS = {"autosave session": True,
            "check update": True,
            "expert mode": False,
            }


class ConfigurationFile(object):
    """Manages a configuration file in the user's config dir"""
    def __init__(self):
        """Initialize configuration file (create if it does not exist)"""
        # get default path of configuration
        udir = appdirs.user_config_dir()
        fname = join(udir, CFGNAME)
        # create file if not existent
        if not os.path.exists(fname):
            # Create the file
            open(fname, "w").close()
        
        self.cfgfile = fname
        self.working_directories = {}


    def load(self):
        """Loads the configuration file returning a dictionary"""
        with io.open(self.cfgfile, 'r') as fop:
            fc = fop.readlines()
        cdict = {}
        for line in fc:
            line = line.strip()
            var, val = line.split("=", 1)
            cdict[var.lower().strip()] = val.strip()
        return cdict
    

    def get_bool(self, key):
        """Returns boolean configuration key"""
        key = key.lower()
        cdict = self.load()
        if key in cdict:
            val = cdict[key]
            msg = "Config key '{}' is not binary (neither 'True' nor 'False')!"
            assert val in ["True", "False"], msg
    
            if val == "True":
                ret = True
            else:
                ret = False
        else:
            ret = DEFAULTS[key]
        return ret
        

    def get_dir(self, name=""):
        """Returns the working directory for label `name`"""
        cdict = self.load()
        wdkey = "working directory {}".format(name.lower())
        
        if wdkey in cdict:
            wd = cdict[wdkey]
        else:
            wd = "./"

        return wd


    def save(self, cdict):
        """Save a configuration dictionary into a file"""
        assert self.cfgfile != "", "Configuration not found: "+self.cfgfile
        skeys = list(cdict.keys())
        skeys.sort()
        outlist = []
        for sk in skeys:
            outlist.append("{} = {}\n".format(sk, cdict[sk]))

        with io.open(self.cfgfile, 'w') as fop:
            fop.writelines(outlist)

    
    def set_bool(self, key, value):
        """Sets boolean key in the configuration file"""
        cdict = self.load()
        cdict[key.lower()] = bool(value)
        self.save(cdict)


    def set_dir(self, wd, name=""):
        """Set the working directory in the configuration file"""
        cdict = self.load()
        wdkey = "working directory {}".format(name.lower())
        cdict[wdkey] = wd
        self.save(cdict)
