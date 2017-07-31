#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - session index handling"""
from __future__ import division, print_function, unicode_literals

from distutils.version import LooseVersion
import copy
import io
import os
from os.path import abspath, basename, join, isdir
import warnings


from .._version import version


def find_data_path(index_item,
                   search_path="./",
                   errors="ignore"):
    """Get the measurement file from entries of an index dictionary
    
    Parameters
    ----------
    index_item: dict
        An index item of one measurement
    search_path: str
        Path to search for the data path
    errors: str
        If the file cannot be found on the file system, then a warning
        is issued if `errors` is set to "ignore", otherwise an IOError
        is raised.
    
    The index dictionary is created for each entry in the
    the index.txt file and contains the keys "name", "fdir", and
    since version 0.6.1 "rdir".
    """
    item = copy.copy(index_item)
    found = False
    
    # file candidates
    mfiles = []
    # absolute path
    mfiles.append(join(item["fdir"], item["name"]))
    # relative paths
    if "rdir" not in item:
        item["rdir"] = "."    
    # Use basename of "fdir" for search, too
    if item["fdir"].count("\\"):
        # Workaround to get basename for files saved
        # with Windows.
        fbase = item["fdir"].rsplit("\\", 1)[1]
    else:
        fbase = basename(item["fdir"])
    dir1 = abspath(join(abspath(search_path), item["rdir"]))
    dir2 = join(dir1, fbase)
    # relative path to zip file
    mfiles.append(join(dir1, item["name"]))
    # relative path tp zip file in subfolder fbase
    mfiles.append(join(dir2, item["name"]))
    
    for mf in mfiles:
        if os.path.exists(mf):
            found = mf
            break

    if not found:
        if errors == "ignore":
            warnings.warn("Could not find file: {}".format(mfiles[0]))
            found = mfiles[0]
        else:
            raise IOError("Could not find file: {}".format(mfiles[0]))

    return found



def index_check(index_file, search_path="./"):
    """Check a session file index for existence of all measurement files"""
    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    missing_files = []
    
    index_dict = index_load(index_file)
    keys = list(index_dict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    keys.sort(key=lambda x: int(x.split("_")[0]))
    for key in keys:    
        item = index_dict[key]
        if not ("special type" in item and
                item["special type"] == "hierarchy child"):
            mfile = find_data_path(item, search_path)
            if not os.path.exists(mfile):
                missing_files.append([key, mfile, item])
    
    messages = {"missing files": missing_files}
    return messages


def index_load(index_file):
    """Load an index file
    
    Parameters
    ----------
    index_file: str
        Path to the index file or folder containing "index.txt".
    
    Returns
    -------
    index_dict: dict
        Dictionary containing all index information
    """
    cfg = {}

    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    with io.open(index_file, 'r') as f:
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


def index_save(index_file, index_dict, save_version=version):
    """Save index dictionary to a file

    Parameters
    ----------
    index_file: str
        Path to index file or folder
    index_dict : dict
        Index dictionary
    """
    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    out = ["# ShapeOut measurement index",
           "# Software version {}".format(save_version)
           ]
    keys = list(index_dict.keys())
    keys.sort()
    for key in keys:
        out.append("[{}]".format(key))
        section = index_dict[key]
        ikeys = list(section.keys())
        ikeys.sort()
        for ikey in ikeys:
            out.append("{} = {}".format(ikey,section[ikey]))
        out.append("")
    
    for i in range(len(out)):
        out[i] = out[i]+"\n"
    with io.open(index_file, "w") as f:
        f.writelines(out)


def index_update(index_file, index_dict):
    """Update an index file with new entries"""
    datadict = index_load(index_file)
    for key in index_dict:
        datadict[key].update(index_dict[key])
    index_save(index_file, datadict)


def index_version(index_file):
    """Obtain the ShapeOut version used to save an index
    
    Parameters
    ----------
    path: str
        Path to an index file or a directory containting "index.txt".

    Returns
    -------
    version: disturils.version.LooseVersion
        The version used
        
    Notes
    -----
    Sessions saved with ShapeOut prior to version 0.7.6 did not
    save the version in the session file and the version is set
    to "0.0.1".
    """
    if isdir(index_file):
        index_file = join(index_file, "index.txt")
    # Obtain version of session
    with io.open(index_file, "r") as fd:
        data = fd.readlines()
    
    for line in data:
        line = line.lower().strip()
        if (line.startswith("#") and 
            line.count("software version")):
            vers = LooseVersion(line.split()[-1])
            break
    else:
        vers = LooseVersion("0.0.1")
    return vers
    