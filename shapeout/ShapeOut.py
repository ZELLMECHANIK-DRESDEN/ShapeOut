#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut

This file initiates the program.

"""
from __future__ import print_function

import multiprocessing as mp
import os
import sys
import wx
import wx.lib.agw.advancedsplash as AS
#import IPython

def findfile(fname):
    """ finds the absolute path of a file
    """
    dirs = list()
    # directory names that make sense
    dirs += [".", "lang", "art", "config"]

    dirs += ["../"+dd for dd in dirs]

    thedirs = []
    if hasattr(sys, 'frozen'):
        for d in dirs:
            d = os.path.join("shapeout-data",d)
            thedirs += [os.path.realpath(os.path.join(sys._MEIPASS,d))]  # @UndefinedVariable
    else:
        for d in dirs:
            thedirs += [os.path.realpath(os.path.join(os.path.dirname(__file__),d))]
    # if this does not work:
    for loc in thedirs:
        thechl = os.path.join(loc,fname)
        if os.path.exists(thechl):
            return thechl
    return ""
   

def main():
    # Note: The order in which the splash screen is initiated and the
    # main app is instantiated is very important:
    # - windows raises an error if wx.App is called too late
    # - ubuntu does not like wx.App before the splash screen
    
    # Start the splash screen in a separate process
    splash = mp.Process(target=splash_show)
    splash.start()

    # first initialize the app to prevent errors in Windows,
    # which is checking some wx runtime variables beforehand.

    app = wx.App(False)

    # Import missing modules
    import codecs
    ## Language support:
    # Go to ../lang and execute
    # python mki18n.py -m
    import gettext
    import platform
    import warnings
    
    import frontend

   
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
        vfile = findfile("version.txt")
        clfile = open(vfile, 'r')
        version = clfile.readline().strip()
        clfile.close()
    except:
        warnings.warn(_("Could not find version file '%(vfile)s'.") % {
                        "vfile": vfile })
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

    # close the splash screen
    splash.terminate()
    # launch application
    app.MainLoop()

    
def splash_show():
    app = wx.App(False)
    # Show the splash screen as early as possible
    img = wx.Image(findfile('logo.png'))
    img.ConvertAlphaToMask()
    bitmap = wx.BitmapFromImage(img)
    frame = wx.Frame(None, -1, "AdvancedSplash Test")
    AS.AdvancedSplash(frame, bitmap=bitmap, 
                agwStyle=AS.AS_NOTIMEOUT|AS.AS_CENTER_ON_SCREEN)
    app.MainLoop()


if __name__ == '__main__':
    # Windows and freezed binaries
    mp.freeze_support()
    if 'unicode' not in wx.PlatformInfo:
        print("\nInstalled version: %s" % wx.version())
        print("A unicode build of wxPython is required for ShapeOut.")
    else:
        main()


