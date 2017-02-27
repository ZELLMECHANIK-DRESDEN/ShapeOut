#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - session handling"""
from __future__ import division, print_function, unicode_literals

from dclab.rtdc_dataset import hashfile
import os
import shutil
import tempfile
import wx
import zipfile

from .. import analysis


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
    tempdir = tempfile.mkdtemp()
    Arc.extractall(tempdir)
    Arc.close()
    
    indexfile = os.path.join(tempdir, "index.txt")

    # check session integrity
    dirname = os.path.dirname(path)
    messages = analysis.session_check_index(indexfile, search_path=dirname)
    
    while len(messages["missing tdms"]):
        # There are missing tdms files. We need to modify the extracted
        # index file with a folder.
        missing = messages["missing tdms"]
        directories = [] # search directories
        updict = {}      # new dicts for individual measurements
        # Ask user for directory
        miss = os.path.basename(missing[0][1])
        
        message = _("ShapeOut could not find the following measurements:")+\
                  "\n\n".join([""]+[m[1] for m in missing]) +"\n\n"+\
                  _("Please select a directory that contains these.")
        
        dlg = wx.MessageDialog(parent,
                               caption=_("Missing tdms files for session"),
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
            key, tdms, thash = m
            newfile = search_hashed_tdms(tdms, thash, directories)
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
        analysis.session_update_index(indexfile, updict)
    
    parent.NewAnalysis(indexfile, search_path=dirname)

    directories = []
    for mm in parent.analysis.measurements:
        if os.path.exists(mm.fdir):
            directories.append(mm.fdir)
    
    bolddirs = parent.analysis.GetTDMSFilenames()

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


def search_hashed_tdms(tdms_file, tdms_hash, directories):
    """ Search `directories` for `tdms_file` with matching `tdms_hash`
    """
    tdms_file = os.path.basename(tdms_file)
    for adir in directories:
        for root, _ds, fs in os.walk(adir):
            if tdms_file in fs:
                this_file = os.path.join(root,tdms_file)
                this_hash = hashfile(this_file)
                if this_hash == tdms_hash:
                    return this_file


