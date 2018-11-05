#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - autosaving of sessions"""
from __future__ import division, print_function, unicode_literals

import os
import time

import wx
import wx.lib.delayedresult as delayedresult

import appdirs

from .. import session
from . import session_ui

cache_dir = appdirs.user_cache_dir(appname="ShapeOut")
autosave_file = os.path.join(cache_dir, "autosave.zmso")


def mkdir_p(adir):
    """Recursively create a directory"""
    adir = os.path.abspath(adir)
    while not os.path.exists(adir):
        try:
            os.mkdir(adir)
        except:
            mkdir_p(os.path.dirname(adir))


def _autosave_consumer(delayedresult, parent):
    if not hasattr(parent, "analysis"):
        # nothing to do
        pass
    else:
        parent.StatusBar.SetStatusText("Autosaving...")
        tempname = autosave_file+".tmp"
        mkdir_p(cache_dir)
        try:
            session.rw.save(tempname, parent.analysis.measurements)
        except session.rw.UnsupportedDataClassSaveError:
            # dictionary data type not supported -> ignore
            parent.StatusBar.SetStatusText("")
        except BaseException:
            raise
            parent.StatusBar.SetStatusText("Autosaving failed!")
        else:
            if os.path.exists(autosave_file):
                os.remove(autosave_file)
            os.rename(tempname, autosave_file)
            parent.StatusBar.SetStatusText("")
        # cleanup when autosave failed
        if os.path.exists(tempname):
            os.remove(tempname)
    autosave_run(parent)


def _autosave_worker(parent, interval):
    """Runs in the background and performs autosaving"""
    time.sleep(interval)


def autosave_run(parent, interval=5):
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
                               caption="Missing data files for session",
                               message=message,
                               style=wx.YES|wx.NO,
                               )
        mod = dlg.ShowModal()
        dlg.Destroy()
        if mod == wx.ID_YES:
            session_ui.open_session_worker(autosave_file, parent)
            return True
    return False
