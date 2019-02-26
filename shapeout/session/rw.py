#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - session saving"""
from __future__ import division, print_function, unicode_literals

import os
import pathlib
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


class SessionIndexFileMissingError(BaseException):
    pass


def load(path, search_path="."):
    """Open a Shape-Out session

    Parameters
    ----------
    path: str
        Path to a Shape-Out session file or a directory containing
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
    path = pathlib.Path(path)
    if path.is_file():
        # extract it first
        arc = zipfile.ZipFile(str(path.resolve()), mode='r')
        tempdir = tempfile.mkdtemp(prefix="ShapeOut-session-load_")
        tempdir = pathlib.Path(tempdir)
        arc.extractall(str(tempdir))
        arc.close()
        cleanup = True
    else:
        tempdir = path
        cleanup = False

    # Support older measurement files
    conversion.compatibilitize_session(str(tempdir),
                                       search_path=str(search_path))

    # load index
    index_file = tempdir / "index.txt"
    if not index_file.exists():
        msg = "Index file must be in {}!".format(tempdir)
        raise SessionIndexFileMissingError(msg)

    index_dict = index.index_load(index_file)

    # Load polygons before importing any data
    polygonfile = tempdir / "PolygonFilters.poly"
    PolygonFilter.clear_all_filters()
    if polygonfile.exists():
        PolygonFilter.import_all(polygonfile)

    # get configurations
    keys = list(index_dict.keys())
    # The identifier (in brackets []) contains a number before the first
    # underscore "_" which determines the order of the plots:
    # keys.sort(key=lambda x: int(x.split("_")[0]))
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
            config_file = tempdir / mm_dict["config"]
            config_dir = config_file.parent
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
                    root_idx_file = config_dir / "_filter_manual_root.npy"
                    if root_idx_file.exists():
                        with root_idx_file.open("rb") as rfd:
                                root_idx = np.load(rfd)
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
            filter_manual_file = config_dir / "_filter_manual.npy"
            if filter_manual_file.exists():
                with filter_manual_file.open("rb") as fafd:
                    mm.filter.manual[:] = np.load(fafd)

            mm.title = mm_dict["title"]
            mm.config.update(cfg)
            mm.apply_filter()
            rtdc_list[kidx] = mm

    if cleanup:
        shutil.rmtree(str(tempdir), ignore_errors=True)
    return rtdc_list


def save(path, rtdc_list):
    """Save a Shape-Out session

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
    path = pathlib.Path(path)
    tempdir = pathlib.Path(tempfile.mkdtemp(prefix="ShapeOut-session-save_"))
    # Dump data into the temporary directory
    index_file = tempdir / "index.txt"
    index_dict = {}

    i = 0
    for mm in rtdc_list:
        if mm.format not in ["hdf5", "hierarchy", "tdms"]:
            msg = "RT-DC dataset must be from data file or hierarchy child!"
            # cleanup
            shutil.rmtree(str(tempdir), ignore_errors=True)
            raise UnsupportedDataClassSaveError(msg)
        i += 1
        ident = "{}_{}".format(i, mm.identifier)
        # the directory in the session zip file where all information
        # will be stored:
        mmdir = tempdir / ident
        while True:
            # If the directory already exists, append a number to that
            # directory to distinguish different measurements.
            g = 0
            if mmdir.exists():
                mmdir = mmdir.with_name(ident + str(g))
                g += 1
            else:
                break
        ident = mmdir.name
        mmdir.mkdir()
        mm_dict = {}
        mm_dict["title"] = mm.title
        mm_dict["hash"] = mm.hash
        mm_dict["identifier"] = mm.identifier
        if mm.format in ["tdms", "hdf5"]:
            mm_dict["name"] = pathlib.Path(mm.path).name
            mm_dict["fdir"] = pathlib.Path(mm.path).parent
            try:
                # On Windows we have multiple drive letters and
                # relpath will complain about that if dirname(mm.path)
                # and rel_path are not on the same drive.
                rdir = str(pathlib.Path(mm.path).relative_to(path.parent))
            except ValueError:
                rdir = "."
            mm_dict["rdir"] = rdir
            # save manual filters file only for real data
            with (mmdir / "_filter_manual.npy").open("wb") as ffd:
                np.save(ffd, mm.filter.manual)
        elif mm.format == "hierarchy":
            pidx = rtdc_list.index(mm.hparent) + 1
            p_ident = "{}_{}".format(pidx, mm.hparent.identifier)
            mm_dict["special type"] = "hierarchy child"
            mm_dict["parent hash"] = mm.hparent.hash
            mm_dict["parent key"] = p_ident
            # save (possibly hidden) root filter indices instead of
            # manual filter array.
            root_idx = mm.filter.retrieve_manual_indices()
            with (mmdir / "_filter_manual_root.npy").open("wb") as rffd:
                np.save(rffd, root_idx)
        # Use forward slash such that sessions saved on Windows
        # can be opened on *nix as well.
        mm_dict["config"] = "{}/config.txt".format(ident)
        index_dict[ident] = mm_dict
        # Save configurations
        cfgfile = mmdir / "config.txt"
        mm.config.save(cfgfile)

    # Write index
    index.index_save(index_file, index_dict)

    # Dump polygons
    if len(PolygonFilter.instances) > 0:
        PolygonFilter.save_all(tempdir / "PolygonFilters.poly")

    # Zip everything
    with zipfile.ZipFile(str(path), mode='w') as arc:
        for root, _dirs, files in os.walk(str(tempdir)):
            for f in files:
                fp = pathlib.Path(root) / f
                if fp.is_file():
                    arc.write(str(fp), str(fp.relative_to(tempdir)))
    # cleanup
    shutil.rmtree(str(tempdir), ignore_errors=True)
