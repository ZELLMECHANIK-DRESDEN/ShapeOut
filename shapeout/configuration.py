#!/usr/bin/python
# -*- coding: utf-8 -*-
""" configuration - configuration file of ShapeOut

"""
from __future__ import division, print_function, unicode_literals

import codecs
import os
from os.path import join

import appdirs

CFGNAME = "shapeout.cfg"

class ConfigurationFile(object):
    """ A fixed configuration file that will be created upon startup.
    
    """
    def __init__(self, path=None):
        """
        """
        # get default path of configuration
        udir = appdirs.user_config_dir()
        fname = join(udir, CFGNAME)

        if not os.path.exists(fname):
            # Create the file
            open(fname, "w").close()
        
        self.cfgfile = fname
        self.working_directories = {}
        self.get_dir()


    def get_dir(self, name=""):
        """ Returns the current working directory """
        with codecs.open(self.cfgfile, 'r', "utf-8") as fop:
            fc = fop.readlines()
        for line in fc:
            line = line.strip()
            if line.split("=")[0].strip() == "Working Directory "+name:
                wd = line.split("=")[1].strip()
                if not os.path.exists(wd):
                    wd = "./"
                break
        else:
            wd = "./"
        return wd


    def set_dir(self, wd, name=""):
        if os.path.exists(wd):
            assert self.cfgfile != "", "Configuration not found: "+self.cfgfile
            with codecs.open(self.cfgfile, 'r', "utf-8") as fop:
                fc = fop.readlines()
            # Check if we have already saved it there.
            wdirin = False
            for i in range(len(fc)):
                if fc[i].split("=")[0].strip() == "Working Directory "+name:
                    fc[i] = u"Working Directory {} = {}".format(name, wd)
                    wdirin = True
            if not wdirin:
                fc.append(u"Working Directory {} = {}".format(name, wd))
            with codecs.open(self.cfgfile, 'w', "utf-8") as fop:
            
                for i in range(len(fc)):
                    fc[i] = fc[i].strip()+"\n"
    
                fop.writelines(fc)
