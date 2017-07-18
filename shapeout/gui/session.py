#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - session handling"""
from __future__ import division, print_function, unicode_literals

from distutils.version import LooseVersion
import os
import shutil
import tempfile
import zipfile

import wx


from ..session.conversion import compatibilitize_session, \
                                 search_hashed_measurement, \
                                 update_session_hashes

from ..session import index


def open_session(path, parent):
    """Open a session file into shapeout
    
    This method performs a lot of logic on `parent`, the
    graphical user interface itself, such as cleanup and
    post-processing steps before and after data import.
    """
    # Cleanup
    delist = [parent, parent.PanelTop, parent.PlotArea]
    for item in delist:
        if hasattr(item, "analysis"):
            del item.analysis
    
    Arc = zipfile.ZipFile(path, mode='r')
    tempdir = tempfile.mkdtemp(prefix="ShapeOut-session_")
    Arc.extractall(tempdir)
    Arc.close()
    
    # The ShapeOut version used to create the session is returned:
    version = compatibilitize_session(tempdir)
    
    indexfile = os.path.join(tempdir, "index.txt")

    # check session integrity
    dirname = os.path.dirname(path)
    messages = index.index_check(indexfile, search_path=dirname)
    while messages["missing files"]:
        # There are missing files. We need to modify the extracted
        # index file with a folder.
        missing = messages["missing files"]
        directories = [] # search directories
        updict = {}      # new dicts for individual measurements
        # Ask user for directory
        miss = os.path.basename(missing[0][1])
        
        message = _("ShapeOut could not find the following measurements:")+\
                  "\n\n".join([""]+[m[1] for m in missing]) +"\n\n"+\
                  _("Please select a directory that contains these.")
        
        dlg = wx.MessageDialog(parent,
                               caption=_("Missing files for session"),
                               message=message,
                               style=wx.CANCEL|wx.OK,
                               )
        mod = dlg.ShowModal()
        dlg.Destroy()
        if mod != wx.ID_OK:
            break
        
        dlg = wx.DirDialog(parent,
                           message=_(
                                    "Please select directory containing {}"
                                    ).format(miss),
                           )
        mod = dlg.ShowModal()
        path = dlg.GetPath()
        dlg.Destroy()
        if mod != wx.ID_OK:
            break

        # Add search directory            
        directories.insert(0, path)
        
        # Try to find all measurements with that directory (also relative)
        wx.BeginBusyCursor()
        remlist = []
        for m in missing:
            key, mfile, index_item = m
            newfile = search_hashed_measurement(mfile,
                                                index_item,
                                                directories,
                                                version=version)
            if newfile is not None:
                newdir = os.path.dirname(newfile)
                updict[key] = {"fdir": newdir}
                directories.insert(0, os.path.dirname(newdir))
                directories.insert(0, os.path.dirname(os.path.dirname(newdir)))
                remlist.append(m)
        for m in remlist:
            missing.remove(m)
        wx.EndBusyCursor()

        # Update the extracted index file.
        index.index_update(indexfile, updict)
    
    # Update hash values of tdms and hierarchy children
    if version < LooseVersion("0.7.6"):
        update_session_hashes(tempdir, search_path=dirname)
    
    parent.NewAnalysis(indexfile, search_path=dirname)

    directories = []
    for mm in parent.analysis.measurements:
        fdir = os.path.dirname(mm.path)
        if os.path.exists(fdir):
            directories.append(fdir)
    
    bolddirs = parent.analysis.GetFilenames()

    parent.OnMenuSearchPathAdd(add=False, path=directories,
                               marked=bolddirs)
    
    # Remove all temporary files
    shutil.rmtree(tempdir, ignore_errors=True)


def save_session(path, analysis):
    # Begin saving
    returnWD = os.getcwd()
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)
    with zipfile.ZipFile(path, mode='w') as arc:
        ## Dump data into directory
        analysis.DumpData(tempdir, rel_path=os.path.dirname(path))
        for root, _dirs, files in os.walk(tempdir):
            for f in files:
                fw = os.path.join(root,f)
                arc.write(os.path.relpath(fw,tempdir))
                os.remove(fw)
    os.chdir(returnWD)
