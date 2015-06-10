#!/usr/bin/python
# -*- coding: utf-8 -*-
""" configuration - configuration file of ShapeOut

"""
from __future__ import division, print_function


import codecs
import os
import sys
import warnings

from ShapeOut import findfile

class ConfigurationFile(object):
    """ A fixed configuration file that will be created upon startup.
    
    """
    def __init__(self):
        # get default path of configuration
        shcfg = "shapeout.cfg"
        fname = findfile(shcfg)
        if not os.path.exists(fname):
            # Create the file
            if hasattr(sys, 'frozen'):
                d = os.path.realpath(os.path.join(sys._MEIPASS,  # @UndefinedVariable
                                                       "shapeout-data"))
                self.cfgfile = os.path.join(d, shcfg)
            else:
                self.cfgfile = os.path.join(os.path.dirname(__file__),
                                                                  shcfg)
            fop = codecs.open(self.cfgfile, 'wb', "utf-8")
            fop.writelines(DefaultConfig)
            fop.close()
        else:
            self.cfgfile = fname

        self.working_directories = {}
        self.GetWorkingDirectory()


    def GetWorkingDirectory(self, name="Main"):
        """ Returns the current working directory """
        wd = default = "./"
        cfgso = self.cfgfile
        path=findfile(cfgso)
        if path == "":
            wd = default
        else:
            fop = codecs.open(path, 'r', "utf-8")
            fc = fop.readlines()
            fop.close()
            for line in fc:
                if line.startswith(("Working Directory "+name).strip()):
                    wd = line.partition("=")[2].strip()
                    if not os.path.exists(wd):
                        wd = default
        self.working_directory = wd
        return wd
        

    def SetWorkingDirectory(self, wd, name="Main"):
        if os.path.exists(wd):
            self.working_directory = wd
            cfgso = self.cfgfile
            path=findfile(cfgso)
            if path == "":
                warnings.warn("Could not find configuration file {}.".
                              format(cfgso))
            fop = codecs.open(path, 'r', "utf-8")
            fc = fop.readlines()
            fop.close()
            wdirin = False
            for i in range(len(fc)):
                if fc[i].startswith("Working Directory "+name):
                    fc[i] = u"Working Directory {} = {}".format(name, wd)
                    wdirin = True
            if not wdirin:
                fc.append(u"Working Directory {} = {}".format(name, wd))
            fop = codecs.open(path, 'w', "utf-8")
            
            for i in range(len(fc)):
                fc[i] = fc[i].strip()+"\n"

            fop.writelines(fc)
            fop.close()

DefaultConfig = ["Working Directory = ./"]

