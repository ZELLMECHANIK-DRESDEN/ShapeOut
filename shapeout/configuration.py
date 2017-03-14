#!/usr/bin/python
# -*- coding: utf-8 -*-
""" configuration - configuration file of ShapeOut

"""
from __future__ import division, print_function, unicode_literals


import codecs
import os
from os.path import abspath, dirname, join
import sys


from util import findfile

class ConfigurationFile(object):
    """ A fixed configuration file that will be created upon startup.
    
    """
    def __init__(self, path=None):
        """
        """
        # get default path of configuration
        shcfg = "shapeout.cfg"
        fname = findfile(shcfg)
        if not os.path.exists(fname):
            # Create the file
            if hasattr(sys, 'frozen'):
                d = abspath(join(sys._MEIPASS,  # @UndefinedVariable
                                 "shapeout-data"))
                self.cfgfile = join(d, shcfg)
            else:
                self.cfgfile = join(abspath(dirname(__file__)), shcfg)
            
            with codecs.open(self.cfgfile, 'wb', "utf-8") as fop:
                fop.writelines(default)

        else:
            self.cfgfile = fname

        self.working_directories = {}
        self.get_dir()


    def get_dir(self, name=""):
        """ Returns the current working directory """
        wd = default = "./"
        cfgso = self.cfgfile
        path=findfile(cfgso)
        if path == "":
            wd = default
        else:
            with codecs.open(path, 'r', "utf-8") as fop:
                fc = fop.readlines()
            for line in fc:
                line = line.strip()
                if line.split("=")[0].strip() == "Working Directory "+name:
                    wd = line.split("=")[1].strip()
                    if not os.path.exists(wd):
                        wd = default
        self.working_directory = wd
        return wd
        

    def set_dir(self, wd, name=""):
        if os.path.exists(wd):
            self.working_directory = wd
            cfgso = self.cfgfile
            path=findfile(cfgso)
            assert path != "", "Configuration not found: "+cfgso
            with codecs.open(path, 'r', "utf-8") as fop:
                fc = fop.readlines()
            # Check if we have already saved it there.
            wdirin = False
            for i in range(len(fc)):
                if fc[i].split("=")[0].strip() == "Working Directory "+name:
                    fc[i] = u"Working Directory {} = {}".format(name, wd)
                    wdirin = True
            if not wdirin:
                fc.append(u"Working Directory {} = {}".format(name, wd))
            fop = codecs.open(path, 'w', "utf-8")
            
            for i in range(len(fc)):
                fc[i] = fc[i].strip()+"\n"

            fop.writelines(fc)
            fop.close()

default = ["Working Directory = ./"]

