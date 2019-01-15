#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - session handling"""
from __future__ import division, print_function, unicode_literals

from distutils.version import LooseVersion
import pathlib
import shutil
import tempfile
import warnings
import zipfile

import wx


from ..session.conversion import compatibilitize_session, \
                                 search_hashed_measurement, \
                                 update_session_hashes

from ..session import index, rw


def open_session(parent, session_file=None):
    """Open a session file into Shape-Out
    
    This is a dialog wrapper for `open_session_worker`. 
    """
    # Determine which session file to open
    if session_file is None:
        # User dialog
        dlg = wx.FileDialog(parent,
                            "Open session file",
                            parent.config.get_path(name="Session"),
                            "",
                            "Shape-Out session (*.zmso)|*.zmso", wx.FD_OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            parent.config.set_path(dlg.GetDirectory(), name="Session")
            fname = dlg.GetPath().encode("utf-8")
            dlg.Destroy()
        else:
            parent.config.set_path(dlg.GetDirectory(), name="Session")
            dlg.Destroy()
            return # nothing more to do here
    else:
        fname = session_file 

    open_session_worker(fname, parent)


def open_session_worker(path, parent):
    """Open a session file into Shape-Out
    
    This method performs a lot of logic on `parent`, the
    graphical user interface itself, such as cleanup and
    post-processing steps before and after data import.
    """
    path = pathlib.Path(path).resolve()
    # Cleanup
    delist = [parent, parent.PanelTop, parent.PlotArea]
    for item in delist:
        if hasattr(item, "analysis"):
            del item.analysis
    
    Arc = zipfile.ZipFile(str(path), mode='r')
    tempdir = tempfile.mkdtemp(prefix="ShapeOut-session_")
    tempdir = pathlib.Path(tempdir)
    Arc.extractall(str(tempdir))
    Arc.close()
    
    # The Shape-Out version used to create the session is returned:
    # Do not perform hash update, because we do not know if all
    # measurement files are where they're supposed to be. 
    version = compatibilitize_session(tempdir, hash_update=False)
    
    index_file = tempdir / "index.txt"
    index_dict = index.index_load(index_file)

    # check session integrity
    dirname = path.parent
    messages = index.index_check(index_file, search_path=dirname)
    while messages["missing files"]:
        # There are missing files. We need to modify the extracted
        # index file with a folder.
        missing = messages["missing files"]
        directories = [] # search directories
        updict = {}      # new dicts for individual measurements
        # Ask user for directory
        miss = missing[0][1].name
        
        message = "Shape-Out could not find the following measurements:"+\
                  "\n\n".join([""]+[str(m[1]) for m in missing]) +"\n\n"+\
                  "Please select a directory that contains these."
        
        dlg = wx.MessageDialog(parent,
                               caption="Missing files for session",
                               message=message,
                               style=wx.CANCEL|wx.OK,
                               )
        mod = dlg.ShowModal()
        dlg.Destroy()
        if mod != wx.ID_OK:
            break
        
        sd = "SessionMissingDirSearch"
        msg = "Please select directory containing {}".format(miss)
        dlg = wx.DirDialog(parent,
                           message=msg,
                           defaultPath=parent.config.get_path(name=sd)
                           )
        mod = dlg.ShowModal()
        path = dlg.GetPath().encode("utf-8")
        parent.config.set_path(wd=path, name=sd)
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
                newdir = newfile.parent
                # Store the original directory name. This is important
                # for sessions stored with Shape-Out version <0.7.6 to
                # correctly compute tdms file hashes.
                updict[key] = {"fdir": str(newdir),
                               "fdir_orig": index_dict[key]["fdir"],
                               }
                remlist.append(m)
        for m in remlist:
            missing.remove(m)
        wx.EndBusyCursor()

        # Update the extracted index file.
        index.index_update(index_file, updict)
    
    # Update hash values of tdms and hierarchy children
    if version < LooseVersion("0.7.6"):
        update_session_hashes(tempdir, search_path=dirname)
    
    # Catch hash comparison warnings and display warning to the user
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter("always", category=rw.HashComparisonWarning)
        rtdc_list = rw.load(tempdir, search_path=dirname)
        if len(ww):
            msg = "One or more files referred to in the chosen session "+\
                  "did not pass the hash check. Nevertheless, Shape-Out "+\
                  "loaded the data. The following warnings were issued:\n"
            msg += "".join([ "\n - "+w.message.message for w in ww ])
            dlg = wx.MessageDialog(None,
                                   msg,
                                   'Hash mismatch warning',
                                   wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()

    parent.NewAnalysis(rtdc_list)

    searchdirs = []
    for mm in parent.analysis.measurements:
        mpath = pathlib.Path(mm.path)
        fdir = mpath.parent
        if fdir.exists():
            searchdirs.append(fdir)
    
    bolddirs = parent.analysis.GetFilenames()

    parent.OnMenuSearchPathAdd(add=False, path=searchdirs,
                               marked=bolddirs)
    
    # Remove all temporary files
    shutil.rmtree(str(tempdir), ignore_errors=True)


def save_session(parent):
    dlg = wx.FileDialog(parent, "Save Shape-Out session", 
                parent.config.get_path(name="Session"), "",
                "Shape-Out session (*.zmso)|*.zmso",
                wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        # Save everything
        path = pathlib.Path(dlg.GetPath().encode("utf-8"))
        dirname = path.parent
        if not path.name.endswith(".zmso"):
            path = dirname / (path.name + ".zmso")
        parent.config.set_path(dirname, name="Session")
        rw.save(path, parent.analysis.measurements)
        return path
    else:
        dirname = dlg.GetDirectory()
        parent.config.set_path(dirname, name="Session")
        dlg.Destroy()
