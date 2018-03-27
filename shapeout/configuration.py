#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration file handling for ShapeOut"""
from __future__ import division, print_function, unicode_literals

import copy
import io
import pathlib

import appdirs

#: default configuration file name
NAME = "shapeout.cfg"

#: default configuration parameters
DEFAULTS = {"autosave session": True,
            "check update": True,
            "expert mode": False,
            }

#: data features only visible in expert mode
EXPERT_FEATURES = ["area_cvx", "area_msd", "frame"]


class ConfigurationFile(object):
    """Manages a configuration file in the user's config dir"""

    def __init__(self, name=NAME, defaults=DEFAULTS, datatype="config"):
        """Initialize configuration file (create if it does not exist)"""
        if datatype == "config":
            udir = appdirs.user_config_dir()
        elif datatype == "cache":
            udir = appdirs.user_cache_dir()
        else:
            raise ValueError("`datatype` must be 'config' or 'cache'.")
        fname = pathlib.Path(udir) / name
        # create file if not existent
        if not fname.exists():
            # Create the file
            fname.open("w").close()

        self.cfgfile = fname
        self.defaults = defaults
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
            if val.lower() not in ["true", "false"]:
                raise ValueError("Config key '{}' not boolean!".format(key))
            if val == "True":
                ret = True
            else:
                ret = False
        else:
            ret = self.defaults[key]
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

    def get_int(self, key):
        """Returns integer configuration key"""
        key = key.lower()
        cdict = self.load()
        if key in cdict:
            val = cdict[key]
            if not val.isdigit():
                raise ValueError("Config key '{}' is no integer!".format(key))
            ret = int(val)
        else:
            raise KeyError("Config key `{}` not set!".format(key))
        return ret

    def save(self, cdict):
        """Save a configuration dictionary into a file"""
        if not self.cfgfile:
            raise ConfigurationFileError("configuration path not set!")
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

    def set_int(self, key, value):
        """Sets integer key in the configuration file"""
        cdict = self.load()
        cdict[key.lower()] = int(value)
        self.save(cdict)


class ConfigurationFileError(BaseException):
    pass


def get_ignored_features():
    """return a list of ignored features

    Features defined in :const:`EXPERT_FEATURES` are returned
    if the expert mode is disabled.
    """
    if ConfigurationFile().get_bool("expert mode"):
        ignored = []
    else:
        # Axes that should not be displayed  by ShapeOut
        ignored = copy.copy(EXPERT_FEATURES)
    return ignored
