#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import io
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
    # bypass "iCCP: known incorrect sRGB profile":
    wx.Log.SetLogLevel(0)
    # first initialize the app to prevent errors in Windows,
    # which is checking some wx runtime variables beforehand.
    app = wx.App(False)
   
    ## initialise language settings:
    try:
        langIni = io.open(findfile("language.ini"), 'r')
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
    
    app.frame = frontend.Frame(version)
    
    return app

if __name__ == "__main__":
    # get session file
    session_file = None
    for arg in sys.argv:
        if arg.endswith(".zmso"):
            print("\nUsing Session "+arg)
            session_file=arg
        else:
            print("Ignoring command line parameter: "+arg)

    app = prepare_app()
    app.frame.InitRun(session_file=session_file)
    app.MainLoop()
