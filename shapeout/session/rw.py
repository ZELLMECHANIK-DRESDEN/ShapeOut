#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - session saving"""
from __future__ import division, print_function, unicode_literals

import os
from os.path import isfile, exists, join
import shutil
import tempfile
import warnings
import zipfile

import numpy as np

from dclab import new_dataset
from dclab.polygon_filter import PolygonFilter
from dclab.rtdc_dataset import Configuration
from . import conversion, index


class HashComparisonWarning(UserWarning):
    pass


class UnsupportedDataClassSaveError(BaseException):
    pass


def load(path, search_path="."):
    """Open a ShapeOut session
    
    Parameters
    ----------
    path: str
        Path to a ShapeOut session file or a directory containing
        the extracted file.
    search_path : str
        Relative search path where to look for measurement files if
        the absolute path stored in index.txt cannot be found.

    Notes
    -----
    This method assumes that the paths of the measurement files can
    be obtained using the data stored in the index file of the session
    and the `search_path` parameter. If this is not the case, please
    use `conversion.search_hashed_measurement`. 
    """
    if isfile(path):
        # extract it first
        arc = zipfile.ZipFile(path, mode='r')
        tempdir = tempfile.mkdtemp(prefix="ShapeOut-session-load_")
        arc.extractall(tempdir)
        arc.close()
        cleanup = True
    else:
        tempdir = path
        cleanup = False

    # Support older measurement files
    conversion.compatibilitize_session(tempdir, search_path=search_path)

    # load index
    index_file = join(tempdir, "index.txt")
    if not exists(index_file):
        raise OSError("Index file must be in {}!".format(tempdir))
    
    index_dict = index.index_load(index_file)

    # Load polygons before importing any data
    polygonfile = os.path.join(tempdir, "PolygonFilters.poly")
    PolygonFilter.clear_all_filters()
    if os.path.exists(polygonfile):
        PolygonFilter.import_all(polygonfile)

    # get configurations
    keys = list(index_dict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    #keys.sort(key=lambda x: int(x.split("_")[0]))
    rtdc_list = [None]*len(keys)
    while rtdc_list.count(None):
        for key in keys:
            # The order in keys is not important to correctly reproduce
            # a session. Important is the integer number before the
            # underscore.
            kidx = int(key.split("_")[0])-1
            if rtdc_list[kidx] is not None:
                # we have already imported that measurement
                continue
            
            mm_dict = index_dict[key]
            # os.path.normpath replaces forward slash with
            # backslash on Windows
            config_file = os.path.normpath(os.path.join(tempdir,
                                                        mm_dict["config"]))
            cfg = Configuration(files=[config_file])

            # Start importing data
            if ("special type" in mm_dict and
                mm_dict["special type"] == "hierarchy child"):
                # check if parent is already here
                pidx = int(mm_dict["parent key"].split("_")[0])-1
                hparent = rtdc_list[pidx]
                if hparent is not None:
                    mm = new_dataset(hparent, identifier=mm_dict["identifier"])
                    # apply manually excluded events
                    root_idx_file = os.path.join(os.path.dirname(config_file),
                                                 "_filter_manual_root.npy")
                    if os.path.exists(root_idx_file):
                        root_idx = np.load(root_idx_file)
                        mm.filter.apply_manual_indices(root_idx)
                else:
                    # parent doesn't exist - try again in next loop
                    continue
            else:
                tloc = index.find_data_path(mm_dict, search_path)
                mm = new_dataset(tloc, identifier=mm_dict["identifier"])
                # Only check for hashes when there is an experimental file
                if mm.hash != mm_dict["hash"]:
                    msg = "File hashes don't match for: {}".format(tloc)
                    warnings.warn(msg, HashComparisonWarning)
            
            # Load manually excluded events
            filter_manual_file = os.path.join(os.path.dirname(config_file),
                                              "_filter_manual.npy")
            if os.path.exists(filter_manual_file):
                mm.filter.manual[:] = np.load(os.path.join(filter_manual_file))

            mm.title = mm_dict["title"]
            mm.config.update(cfg)
            mm.apply_filter()
            rtdc_list[kidx] = mm
    
    if cleanup:
        shutil.rmtree(tempdir, ignore_errors=True)
    return rtdc_list


def save(path, rtdc_list):
    """Save a ShapeOut session
    
    Parameters
    ----------
    path: str
        Path to a file where the session will be saved.
    rtdc_list: list of RTDCBase instances
        The measurements to save in the session
        
    
    Notes
    -----
    The session file is a .zip file with an index and all
    relevant configuration data to reproduce the list of
    RTDCBase instances. 
    """
    tempdir = tempfile.mkdtemp(prefix="ShapeOut-session-save")
    returnWD = os.getcwd()
    os.chdir(tempdir)
    # Dump data into the temporary directory
    index_file = os.path.join(tempdir, "index.txt")
    index_dict = {}
    
    i = 0
    for mm in rtdc_list:
        if mm.format not in ["hdf5", "hierarchy", "tdms"]:
            msg = "RT-DC dataset must be from data file or hierarchy child!"
            raise UnsupportedDataClassSaveError(msg)
        i += 1
        ident = "{}_{}".format(i, mm.identifier)
        # the directory in the session zip file where all information
        # will be stored:
        mmdir = os.path.join(tempdir, ident)
        while True:
            # If the directory already exists, append a number to that
            # directory to distinguish different measurements.
            g=0
            if os.path.exists(mmdir):
                mmdir = mmdir+str(g)
                ident = os.path.split(mmdir)[1]
                g += 1
            else:
                break
        os.mkdir(mmdir)
        mm_dict = {}
        mm_dict["title"] = mm.title
        mm_dict["hash"] = mm.hash
        mm_dict["identifier"] = mm.identifier
        if mm.format in ["tdms", "hdf5"]:
            mm_dict["name"] = os.path.basename(mm.path)
            mm_dict["fdir"] = os.path.dirname(mm.path)
            try:
                # On Windows we have multiple drive letters and
                # relpath will complain about that if dirname(mm.path)
                # and rel_path are not on the same drive.
                rel_path = os.path.dirname(path)
                rdir = os.path.relpath(os.path.dirname(mm.path), rel_path)
            except ValueError:
                rdir = "."
            mm_dict["rdir"] = rdir
            # save manual filters file only for real data
            np.save(os.path.join(mmdir, "_filter_manual.npy"), mm.filter.manual)
        elif mm.format == "hierarchy":
            pidx = rtdc_list.index(mm.hparent) + 1
            p_ident = "{}_{}".format(pidx, mm.hparent.identifier)
            mm_dict["special type"] = "hierarchy child"
            mm_dict["parent hash"] = mm.hparent.hash
            mm_dict["parent key"] = p_ident
            # save (possibly hidden) root filter indices instead of
            # manual filter array.
            root_idx = mm.filter.retrieve_manual_indices()
            np.save(os.path.join(mmdir, "_filter_manual_root.npy"), root_idx)
        # Use forward slash such that sessions saved on Windows
        # can be opened on *nix as well.
        mm_dict["config"] = "{}/config.txt".format(ident)
        index_dict[ident] = mm_dict
        # Save configurations
        cfgfile = os.path.join(mmdir, "config.txt")
        mm.config.save(cfgfile)

    # Write index
    index.index_save(index_file, index_dict)
    
    # Dump polygons
    if len(PolygonFilter.instances) > 0:
        PolygonFilter.save_all(os.path.join(tempdir,
                               "PolygonFilters.poly"))

    # Zip everything    
    with zipfile.ZipFile(path, mode='w') as arc:
        for root, _dirs, files in os.walk(tempdir):
            for f in files:
                fw = os.path.join(root,f)
                arc.write(os.path.relpath(fw,tempdir))
                os.remove(fw)
    os.chdir(returnWD)
    # cleanup
    shutil.rmtree(tempdir, ignore_errors=True)

