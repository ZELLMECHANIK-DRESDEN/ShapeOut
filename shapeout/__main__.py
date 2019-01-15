#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import warnings
import wx

# This must be done _before_ any widget imports in your application,
# including importing pyface.api. Precisely, this must be set before
# the first import of pyface.toolkit.
import traits.etsconfig.api
traits.etsconfig.api.ETSConfig.toolkit = 'wx'

from .gui import frontend


def prepare_app():
    # bypass "iCCP: known incorrect sRGB profile":
    wx.Log.SetLogLevel(0)
    # first initialize the app to prevent errors in Windows,
    # which is checking some wx runtime variables beforehand.
    app = wx.App(False)
   
    # get version
    try:
        from ._version import version
    except:
        warnings.warn("Could not determine Shape-Out version.")
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
