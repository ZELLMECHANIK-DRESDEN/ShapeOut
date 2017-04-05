#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - session handling"""
from __future__ import division, print_function, unicode_literals

import codecs
from dclab.rtdc_dataset import hashfile
import os
import shutil
import tempfile
import warnings
import wx
import zipfile



def get_tdms_file(index_dict,
                  search_path="./",
                  errors="ignore"):
    """ Get the tdms file from entries in the index dictionary
    
    The index dictionary is created from each entry in the
    the index.txt file and contains the keys "name", "fdir", and
    since version 0.6.1 "rdir".
    
    If the file cannot be found on the file system, then a warning
    is issued if `errors` is set to "ignore", otherwise an IOError
    is raised.
    
    """
    found = False
    tdms1 = os.path.join(index_dict["fdir"], index_dict["name"])
    
    if os.path.exists(tdms1):
        found = tdms1
    else:
        if "rdir" in index_dict:
            # try to find relative path
            sdir = os.path.abspath(search_path)
            ndir = os.path.abspath(os.path.join(sdir, index_dict["rdir"]))
            tdms2 = os.path.join(ndir, index_dict["name"])
            if os.path.exists(tdms2):
                found = tdms2
    
    if not found:
        if errors == "ignore":
            warnings.warn("Could not find file: {}".format(tdms1))
            found = tdms1
        else:
            raise IOError("Could not find file: {}".format(tdms1))

    return found


def index_check(indexname, search_path="./"):
    """ Check a session file index for existence of all measurement files
    """
    missing_files = []
    
    datadict = index_load(indexname)
    keys = list(datadict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    keys.sort(key=lambda x: int(x.split("_")[0]))
    for key in keys:    
        data = datadict[key]
        if not ("special type" in data and
                data["special type"] == "hierarchy child"):
            tdms = get_tdms_file(data, search_path)
            if not os.path.exists(tdms):
                missing_files.append([key, tdms, data["tdms hash"]])
    
    messages = {"missing tdms": missing_files}
    return messages


def index_load(cfgfilename):
    """ Load a configuration file
    
    
    Parameters
    ----------
    cfgfilename : absolute path
        Filename of the configuration
    
    Returns
    -------
    cfg : dict
        Dictionary with configuration
    """
    cfg = {}

    with codecs.open(cfgfilename, 'r', 'utf-8') as f:
        code = f.readlines()
    
    for line in code:
        # We deal with comments and empty lines
        # We need to check line length first and then we look for
        # a hash.
        line = line.split("#")[0].strip()
        if len(line):
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                if not section in cfg:
                    cfg[section] = {}
                continue
            var, val = line.split("=", 1)
            var, val = var.strip(), val.strip()
            if len(var) != 0 and len(str(val)) != 0:
                cfg[section][var] = val

    return cfg


def index_save(indexname, datadict):
    """ Save configuration to text file


    Parameters
    ----------
    indexname : absolute path
        Filename of the configuration
    datadict : dict
        Dictionary containing configuration.

    """
    out = []
    keys = list(datadict.keys())
    keys.sort()
    for key in keys:
        out.append("[{}]".format(key))
        section = datadict[key]
        ikeys = list(section.keys())
        ikeys.sort()
        for ikey in ikeys:
            out.append("{} = {}".format(ikey,section[ikey]))
        out.append("")
    
    with codecs.open(indexname, "wb", "utf-8") as f:
        for i in range(len(out)):
            out[i] = out[i]+"\r\n"
        f.writelines(out)


def index_update(indexname, updict={}):
    datadict = index_load(indexname)
    for key in updict:
        datadict[key].update(updict[key])
    index_save(indexname, datadict)


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
    messages = index_check(indexfile, search_path=dirname)
    
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
        index_update(indexfile, updict)
    
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
