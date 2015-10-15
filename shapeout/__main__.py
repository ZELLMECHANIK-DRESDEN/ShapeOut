#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import codecs
## Language support:
# Go to ../lang and execute
# python mki18n.py -m
import gettext
import os
import platform
import sys
import warnings
import wx

from .gui import frontend
from .util import findfile

def prepare_app():
    # first initialize the app to prevent errors in Windows,
    # which is checking some wx runtime variables beforehand.
    app = wx.App(False)
   
    ## initialise language settings:
    try:
        langIni = codecs.open(findfile("language.ini"), 'r', 'utf-8')
    except IOError:
        language = u'en' #defaults to english
    else:
        language = langIni.read().strip()

    locales = {
        u'en' : (wx.LANGUAGE_ENGLISH, u'en_US.UTF-8'),
        u'de' : (wx.LANGUAGE_GERMAN, u'de_DE.UTF-8'),
        }
    mylocale = wx.Locale(locales[language][0], wx.LOCALE_LOAD_DEFAULT)
    langdir = findfile("locale")
    
    
    Lang = gettext.translation(u'lang', langdir,
                 languages=[mylocale.GetCanonicalName()], fallback=True)
                 
    Lang.install(unicode=1)
    if platform.system() == 'Linux':
        try:
            # to get some language settings to display properly:
            os.environ['LANG'] = locales[language][1]

        except (ValueError, KeyError):
            pass

    # get version
    try:
        from ._version import version
    except:
        warnings.warn(_("Could not determine ShapeOut version."))
        version = None
    
    # get session file
    sessionfile = None
    for arg in sys.argv:
        if arg.endswith(".zmso"):
            print("\nLoading Session "+arg)
            sessionfile=arg
        else:
            print("Ignoring command line parameter: "+arg)

    app.frame = frontend.Frame(version, sessionfile = sessionfile)
    
    return app

if __name__ == "__main__":
    app = prepare_app()
    app.MainLoop()
