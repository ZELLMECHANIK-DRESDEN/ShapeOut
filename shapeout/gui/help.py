#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - help menu content"""
from __future__ import division, print_function, unicode_literals

import importlib
import sys
import webbrowser
import wx

from . import misc
from .._version import version 


def about(version=version):
    """Displays the about dialog"""
    description =  ("Shape-Out is a data evaluation tool"+
        "\nfor real-time deformability cytometry (RT-DC)."+
        "\nShape-Out is written in Python.")
    licence = """Shape-Out is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published 
by the Free Software Foundation, either version 2 of the License, 
or (at your option) any later version.

Shape-Out is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License 
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
    info = wx.AboutDialogInfo()
    #info.SetIcon(wx.Icon('hunter.png', wx.BITMAP_TYPE_PNG))
    info.SetName('Shape-Out')
    info.SetVersion(version)
    info.SetDescription(description)
    info.SetCopyright(u'(C) 2015 Paul Müller')
    info.SetWebSite(u"http://zellmechanik.com/")
    info.SetLicence(licence)
    info.SetIcon(misc.getMainIcon(pxlength=64))
    info.AddDeveloper(u'Paul Müller')
    info.AddDeveloper(u'Maik Herbig')
    info.AddDeveloper(u'Philipp Rosendahl')
    info.AddDocWriter(u'Paul Müller')
    wx.AboutBox(info)


def docs(version=version):
    """Display the online documentation"""
    if version.count("post"):
        tag = "develop"
    else:
        tag = version
    url = "https://shapeout.readthedocs.io/en/{}/".format(tag)
    webbrowser.open(url)

    
def software():
    """Displays the software dialog"""
    # Version information
    vinfo = [
             ["appdirs", "appdirs", "__version__"],
             ["chaco", "chaco", "__version__"],
             ["dclab", "dclab", "__version__"],
             ["fcswrite", "fcswrite", "__version__"],
             ["imageio", "imageio", "__version__"],
             ["npTDMS", "nptdms", "__version__"],
             ["NumPy", "numpy", "__version__"],
             ["pyper", "pyper", "__version__"],
             ["SciPy", "scipy", "__version__"],
             ["simplejson", "simplejson", "__version__"],
             ["wxPython", "wx", "__version__"],
             ]

    from ..util import cran
    r_version = cran.get_R_version()
    
    text = "Shape-Out "+version+\
           "\n\nPython "+sys.version+\
           "\n\nModules:"
    for v in vinfo:
        vii = getattr(importlib.import_module(v[1]), v[2])
        text += "\n - {} {}".format(v[0], vii)
           
    if hasattr(sys, 'frozen'):
        pyinst = "\n\n"
        pyinst += "This executable has been created using PyInstaller."
        text += pyinst
        if 'Anaconda' in sys.version or "Continuum Analytics" in sys.version:
            conda = "\n\nPowered by Anaconda"
            text += conda
    
    mtext = "\n\n"
    mtext += "Other software:\n"
    mtext += "\n".join([ "  "+r for r in r_version.split("\n")])
    text += mtext
    
    wx.MessageBox(text, 'Software', wx.OK|wx.ICON_INFORMATION)
