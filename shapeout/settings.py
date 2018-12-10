#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - Settings file management"""
from __future__ import division, print_function

import copy
import pathlib

import appdirs

#: default settings file name
NAME = "shapeout.cfg"

#: default configuration parameters
DEFAULTS = {"autosave session": True,
            "check update": True,
            "expert mode": False,
            }

#: data features only visible in expert mode
EXPERT_FEATURES = ["area_cvx",
                   "area_msd",
                   "frame",
                   "inert_ratio_prnc",
                   "tilt",
                   ]


class SettingsFile(object):
    """Manages a settings file in the user's config dir"""

    def __init__(self, name=NAME, defaults=DEFAULTS, directory=None):
        """Initialize settings file (create if it does not exist)"""
        if directory is None:
            directory = appdirs.user_config_dir()
        fname = pathlib.Path(directory) / name
        # create file if not existent
        if not fname.exists():
            # Create the file
            fname.open("w").close()

        self.cfgfile = fname
        self.defaults = defaults
        self.working_directories = {}

    def load(self):
        """Loads the settings file returning a dictionary"""
        with self.cfgfile.open() as fop:
            fc = fop.readlines()
        cdict = {}
        for line in fc:
            line = line.strip()
            data = line.split("=", 1)
            if len(data) == 2:
                # Only unpack data if there is a key-value pair
                # (Avoids ValueError when for some reason the value
                # is missing).
                var, val = data
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

    def get_path(self, name=""):
        """Returns the path for label `name`"""
        cdict = self.load()
        wdkey = "path {}".format(name.lower())

        if wdkey in cdict:
            wd = cdict[wdkey]
        else:
            wd = "./"

        return wd

    def save(self, cdict):
        """Save a settings dictionary into a file"""
        if not self.cfgfile:
            raise SettingsFileError("Settings path not set!")
        skeys = list(cdict.keys())
        skeys.sort()
        outlist = []
        for sk in skeys:
            sval = cdict[sk]
            if isinstance(sval, str):
                sval = sval.decode("utf-8")
            elif isinstance(sval, pathlib.Path):
                sval = str(sval).decode("utf-8")
            outlist.append(u"{} = {}\n".format(sk, sval))

        with self.cfgfile.open('w') as fop:
            fop.writelines(outlist)

    def set_bool(self, key, value):
        """Sets boolean key in the settings file"""
        cdict = self.load()
        cdict[key.lower()] = bool(value)
        self.save(cdict)

    def set_int(self, key, value):
        """Sets integer key in the settings file"""
        cdict = self.load()
        cdict[key.lower()] = int(value)
        self.save(cdict)

    def set_path(self, wd, name=""):
        """Set the path in the settings file"""
        cdict = self.load()
        wdkey = "path {}".format(name.lower())
        cdict[wdkey] = wd
        self.save(cdict)


class SettingsFileCache(SettingsFile):
    """A SettingsFile-based data cache"""
    def __init__(self, name):
        directory = appdirs.user_cache_dir()
        super(SettingsFileCache, self).__init__(name=name,
                                                defaults={},
                                                directory=directory)


class SettingsFileError(BaseException):
    pass


def get_ignored_features():
    """return a list of ignored features

    Features defined in :const:`EXPERT_FEATURES` are returned
    if the expert mode is disabled.
    """
    if SettingsFile().get_bool("expert mode"):
        ignored = []
    else:
        # Axes that should not be displayed  by Shape-Out
        ignored = copy.copy(EXPERT_FEATURES)
    return ignored
