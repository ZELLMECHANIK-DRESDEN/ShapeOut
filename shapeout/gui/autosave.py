#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - autosaving of sessions
"""
from __future__ import division, print_function

import appdirs
import os
import shutil
import time
import wx
import wx.lib.delayedresult as delayedresult

from . import session

cache_dir = appdirs.user_cache_dir(appname="ShapeOut")
autosave_file = os.path.join(cache_dir, "autosave.zmso")


def mkdir_p(adir):
    """Recursively create a directory"""
    adir = os.path.abspath(adir)
    if not os.path.exists(adir):
        try:
            os.mkdir(adir)
        except:
            mkdir_p(os.path.dirname(adir))


def _autosave_consumer(delayedresult, parent):
    parent.StatusBar.SetStatusText("Autosaving...")
    tempname = autosave_file+".tmp"
    mkdir_p(cache_dir)
    session.save_session(tempname, parent.analysis)
    try:
        session.save_session(tempname, parent.analysis)
    except:
        parent.StatusBar.SetStatusText("Autosaving failed!")
        shutil.rmtree(tempname, ignore_errors=True)
    else:
        os.rename(tempname, autosave_file)
        parent.StatusBar.SetStatusText("")
    autosave_run(parent)


def _autosave_worker(parent, interval):
    """Runs in the background and performs autosaving"""
    time.sleep(interval)


def autosave_run(parent, interval=60):
    """Runs in the background and performs autosaving"""
    delayedresult.startWorker(_autosave_consumer,
                              _autosave_worker,
                              wargs=(parent, interval,),
                              cargs=(parent,))


def check_recover(parent):
    """Check for a recovery file and ask if user wants to restore
    
    Returns True if a session was restored. False otherwise.
    """
    if os.path.exists(autosave_file):
        message="Autosaved session found. Restore?"
        dlg = wx.MessageDialog(parent,
                               caption=_("Missing tdms files for session"),
                               message=message,
                               style=wx.YES|wx.NO,
                               )
        mod = dlg.ShowModal()
        dlg.Destroy()
        if mod != wx.YES:
            session.open_session(autosave_file, parent)
            return True
    return False
