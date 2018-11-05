#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out launcher with splash screen"""
from __future__ import print_function

import multiprocessing as mp
from os.path import abspath, dirname, join
import pkg_resources
import sys

import wx
import wx.lib.agw.advancedsplash as AS

sys.path.insert(0, dirname(dirname(abspath(__file__))))


def main():
    # Note: The order in which the splash screen is initiated and the
    # main app is instantiated is very important:
    # - windows raises an error if wx.App is called too late
    # - ubuntu does not like wx.App before the splash screen
    
    # Start the splash screen in a separate process
    
    splash = mp.Process(target=splash_show)
    splash.start()

    sys.path.insert(0, dirname(dirname(abspath(__file__))))
    from shapeout.__main__ import prepare_app
    app = prepare_app()

    # close the splash screen
    splash.terminate()
    # launch application
    app.frame.InitRun()
    app.MainLoop()
    
    
def splash_show():
    # bypass "iCCP: known incorrect sRGB profile":
    wx.Log.SetLogLevel(0)
    # setup splash app
    app = wx.App(False)
    # Show the splash screen as early as possible
    imdir = pkg_resources.resource_filename("shapeout", "img")
    img = wx.Image(join(imdir, 'zm_logo_small_bgwhite.png'))
    # alpha mask is only binary - don't use it, looks ugly.
    #img.ConvertAlphaToMask()
    bitmap = wx.BitmapFromImage(img)
    frame = wx.Frame(None, -1, "Shape-Out Splash Screen")
    AS.AdvancedSplash(frame, bitmap=bitmap, 
                      agwStyle=AS.AS_NOTIMEOUT|AS.AS_CENTER_ON_SCREEN
                      )
    app.MainLoop()


if __name__ == '__main__':
    # Windows and freezed binaries
    mp.freeze_support()
    if 'unicode' not in wx.PlatformInfo:
        print("\nInstalled version: %s" % wx.version())
        print("A unicode build of wxPython is required for Shape-Out.")
    else:
        main()
