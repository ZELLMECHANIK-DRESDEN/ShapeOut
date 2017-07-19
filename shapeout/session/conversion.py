#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - session conversion

Due to changes in naming conventions and refactoring in dclab,
the data stored in ShapeOut sessions depends on the the version
of dclab that was used at the time the session was saved.
ShapeOut releases come as Windows installers that contain a
specific version of dclab. Starting version 0.7.6, this
version is stored along with the session and it is used to
decide which parts of the session data needs conversion to
work with the current version of ShapeOut.
"""
from __future__ import division, print_function, unicode_literals

from distutils.version import LooseVersion
import io
import hashlib
import os
from os.path import dirname, exists, join
import re
import sys

if sys.version_info[0] == 2:
    str_classes = (str, unicode)
else:
    str_classes = str

import numpy as np

import dclab
from dclab.rtdc_dataset.config import Configuration

from . import index

# Column name replacements, see
# https://github.com/ZELLMECHANIK-DRESDEN/dclab/issues/16
# https://github.com/ZELLMECHANIK-DRESDEN/rtdc_hdf5/issues/5
compat_replace = [
                  ["area ratio", "area_ratio"],
                  ["area", "area_um"],
                  ["areapix", "area_cvx"],
                  ["arearaw", "area_msd"],
                  ["brightness", "bright_avg"],
                  ["brightnesssd", "bright_sd"],
                  ["inertia ratio", "inert_ratio"],
                  ["inertia ratio raw", "inert_ratio_raw"],
                  ["defo", "deform"],
                  ["fl-1area", "fl1_area"],
                  ["fl-1max", "fl1_max"],
                  ["fl-1dpeaks", "fl1_dist"],
                  ["fl-1width", "fl1_width"],
                  ["fl-1npeaks", "fl1_npeaks"],
                  ["fl-1pos", "fl1_pos"],
                  ["fl-2area", "fl2_area"],
                  ["fl-2max", "fl2_max"],
                  ["fl-2dpeaks", "fl2_dist"],
                  ["fl-2width", "fl2_width"],
                  ["fl-2npeaks", "fl2_npeaks"],
                  ["fl-2pos", "fl2_pos"],
                  ["fl-3area", "fl3_area"],
                  ["fl-3max", "fl3_max"],
                  ["fl-3dpeaks", "fl3_dist"],
                  ["fl-3width", "fl3_width"],
                  ["fl-3npeaks", "fl3_npeaks"],
                  ["fl-3pos", "fl3_pos"],
                  ["pos x", "pos_x"],
                  ["pos lat", "pos_y"],
                  ["x-size", "size_x"],
                  ["y-size", "size_y"],
                  ]


def ci_replace(data, old, new):
    """Case insensitive replacement in strings"""
    pattern = re.compile(old, re.IGNORECASE)
    return pattern.sub(new, data)


def ci_rm_row(data, ident):
    """Case insensitive removal of a row contained in data"""
    data = data.split("\n")
    newdata = []
    for ii in range(len(data)):
        if data[ii].lower().count(ident.lower()) == 0:
            newdata.append(data[ii])
    return "\n".join(newdata)



def hashfile_sha(fname, blocksize=65536):
    """Compute sha256 hex-hash of a file
    
    Parameters
    ----------
    fname: str
        path to the file
    blocksize: int
        block size read from the file
    count: int
        number of blocks read from the file
    """
    hasher = hashlib.sha256()
    with io.open(fname, 'rb') as fd:
        buf = fd.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fd.read(blocksize)
    return hasher.hexdigest()


def old_tdms_saved_hash(index_item):
    """Compute md5 hash from data stored in old session index"""
    fd = index_item["fdir"]
    ff = index_item["name"]

    if fd.count(":\\"):
        tdms_path = fd + "\\" + ff
        mx = fd + "\\" +  ff.split("_")[0]
    else:
        tdms_path = join(fd, ff)
        mx = join(fd, ff.split("_")[0])

    
    file_hashes = [(tdms_path, index_item["tdms hash"]),
                   (mx+"_camera.ini", index_item["camera.ini hash"]),
                   (mx+"_para.ini", index_item["para.ini hash"])
                   ]

    ihasher = hashlib.md5()
    ihasher.update(obj2str(tdms_path))
    ihasher.update(obj2str(file_hashes))
    return ihasher.hexdigest()


def compatibilitize_session(tempdir, hash_update=True, search_path="."):
    """Update extracted files to latest format
    
    ShapeOut 0.5.7
      - title saved in index.txt
    
    ShapeOut 0.7.1
      - change names of KDE accuracies
        (kde multivariate -> kde accuracy)
    
    ShapeOut 0.7.4
      - rewrite config.txt path to always use slash
    
    ShapeOut 0.7.5
      - remove emodulus computation parameters if accuracy not present
    
    ShapeOut 0.7.6
      - introduction of new column names in dclab 0.2.5
      - all previous version did not support manual filters in
        hierarchy children (remove the _filter_manual.npy file)
      - update session hashes (if `hash_update` is set to `True`)

    ShapeOut 0.7.8
      - introduction of new key "identifier" in mm_dict
      - replace "parent id" key with "parent key" in hierarchy children


    Parameters
    ----------
    tempdir: str
        Path to the directory containing the extracted session
    hash_update: bool
        Update the session hashes for sessions from version <0.7.6
    search_path: str
        Search path for measurement files used when `hash_update`
        is `True`.

    See Also
    --------
    update_session_hashes: Update hashes for RT-DC datasets/hierarchies
    """
    version = index.index_version(tempdir)
    
    # Find all config.txt files and replace column names
    change_configs = []
    for root, _d, fs in os.walk(tempdir):
        for f in fs:
            if f == "config.txt":
                change_configs.append(os.path.join(root, f))

    # Add title to index
    if version < LooseVersion("0.5.7"):
        index_dict = index.index_load(tempdir)
        for key in index_dict:
            if "title" not in index_dict[key]:
                index_dict[key]["title"] = "no title"
        index.index_save(tempdir, index_dict)

    for cc in change_configs:
        with io.open(cc) as fd:
            data = fd.read()
        
        if version < LooseVersion("0.7.1"):
            data = ci_replace(data, "\nkde multivariate ", "\nkde accuracy ")
        
        
        if version < LooseVersion("0.7.5"):
            if data.count("kde accuracy emodulus") == 0:
                data = ci_rm_row(data, "emodulus medium ")
                data = ci_rm_row(data, "emodulus model ")
                data = ci_rm_row(data, "emodulus temperature ")
                data = ci_rm_row(data, "emodulus viscosity ")

        if version < LooseVersion("0.7.6"):
            for old, new in compat_replace:
                for pattern in ["\n{} min = ",
                                "\n{} max = ",
                                "\naxis x = {}\n",
                                "\naxis y = {}\n",
                                "\ncontour accuracy {} = ",
                                "\nkde accuracy {} = ",
                                ]:
    
                    data = ci_replace(data,
                                      pattern.format(old),
                                      pattern.format(new))

        
        with io.open(cc, "w") as fd:
            fd.write(data)

    # Change polygon filters as well
    pfile = os.path.join(tempdir, "PolygonFilters.poly")
    if os.path.exists(pfile):
        with io.open(pfile) as fd:
            datap = fd.read()
            
        if version < LooseVersion("0.7.6"):
            for old, new in compat_replace:
                for pattern in ["\nx axis = {}\n",
                                "\ny axis = {}\n",
                                ]:
                    datap = ci_replace(datap,
                                       pattern.format(old),
                                       pattern.format(new))
        
        with io.open(pfile, "w") as fd:
            fd.write(datap)

    
    # Rewrite confix.txt path
    if version < LooseVersion("0.7.4"):
        index_dict = index.index_load(tempdir)
        for key in index_dict:
            repl = index_dict[key]["config"].replace("\\config.txt",
                                                     "/config.txt")
            index_dict[key]["config"] = repl
        index.index_save(tempdir, index_dict)


    # Remove _filter_manual.npy of hierarchy children
    # These were actually not supported but stored anyway and sometimes
    # with a wrong size.
    if version < LooseVersion("0.7.6"):
        index_dict = index.index_load(tempdir)
        for key in index_dict:
            if "special type" in index_dict[key]:
                filtman = join(join(tempdir, key), "_filter_manual.npy")
                if exists(filtman):
                    os.remove(filtman)

    # Update file hashes
    # This only works if the absolute or relative paths in the index
    # are correct.
    if hash_update:
        if version < LooseVersion("0.7.6"):
            update_session_hashes(tempdir, search_path=search_path)


    # Add "identifier" and replace "parent id" with "parent key"
    if version < LooseVersion("0.7.8"):
        index_dict = index.index_load(tempdir)
        for key in index_dict:
            index_dict[key]["identifier"] = key
            if "parent id" in index_dict[key]:
                pkey = index_dict[key].pop("parent id")
                index_dict[key]["parent key"] = pkey
        index.index_save(tempdir, index_dict)

    return version


def obj2str(obj):
    """String representation of an object for hashing"""
    if isinstance(obj, str_classes):
        return obj.encode("utf-8")
    elif isinstance(obj, (bool, int, float)):
        return str(obj).encode("utf-8")
    elif obj is None:
        return b"none"
    elif isinstance(obj, np.ndarray):
        return obj.tostring()
    elif isinstance(obj, tuple):
        return obj2str(list(obj))
    elif isinstance(obj, list):
        return b"".join(obj2str(o) for o in obj)
    elif isinstance(obj, dict):
        return obj2str(list(obj.items()))
    elif hasattr(obj, "identifier"):
        return obj2str(obj.identifier)
    else:
        raise ValueError("No rule to convert object '{}' to string.".
                         format(obj.__class__))


def update_session_hashes(tempdir, search_path="."):
    """Find all hierarchy children and compute correct hash
    
    - Replace old hashes with new hashes
    - Fix some (not all) hierarchy problems
    
    New hashing methods were introduced in ShapeOut 0.7.6.
    Do not call this method for later sessions.

    This method assumes that the paths to the measurement files
    are correct. It is therefore not included in the
    `compatibilitize_session` method.
    """
    index_dict = index.index_load(tempdir)
    parents = []
    children = []
    for key in index_dict:
        if "special type" in index_dict[key]:
            children.append(key)
        else:
            parents.append(key)


    datasets = {}
    hashes = {}
    # First compute old and new hashes of the parents
    for pp in parents:
        item = index_dict[pp]
        path = index.find_data_path(item, search_path=search_path)
        assert "tdms hash" in item
        # We have two ways to check data hashes
        old = old_tdms_saved_hash(item)
        cfgfile = join(tempdir, item["config"])
        cfg = Configuration(files=[cfgfile])
        mm = dclab.new_dataset(path)
        mm.config.update(cfg)
        mm.apply_filter()
        datasets[pp] = mm
        # record parent hashes
        hashes[pp]=[old, mm.hash]

        index_dict[pp].pop("tdms hash")
        index_dict[pp].pop("camera.ini hash")
        index_dict[pp].pop("para.ini hash")
        index_dict[pp]["hash"] = mm.hash
        index_dict[pp]["fdir"] = dirname(path)


    # As long as there are children, iteratively search
    # for their parents.
    found = []
    for ch in children:
        item = index_dict[ch]
        # Get configuration of child
        cfgfile = join(tempdir, item["config"])
        cfg = Configuration(files=[cfgfile])
        hparent = cfg["filtering"]["hierarchy parent"]
        # Search for hash and replace in dict
        for key in list(hashes.keys()):
            if hashes[key][0] == hparent:
                found.append(ch)
                mm_p = datasets[key]
                mm = dclab.new_dataset(mm_p)
                mm.config.update(cfg)
                datasets[ch] = mm
                # Update configuration file
                cfg["filtering"]["hierarchy parent"] = mm_p.identifier
                cfg.save(cfgfile)
                # Update hashes dictionary
                hashes[ch] = [old, mm.hash]
                # Update index dictionary
                index_dict[ch]["parent hash"] = hashes[key][1]
                index_dict[ch]["hash"] = mm.hash
                index_dict[ch]["parent key"] = key
                break

    # Remove found children from list
    for ch in found:
        children.remove(ch)

    if children:
        # There is a deep hierarchy. In previous versions of
        # ShapeOut, the parent of a children was identified
        # with the identifier. However, the identifier of children
        # was generated with a hash containing time and thus it
        # is not possible to reconstruct this identifier. We
        # could only guess which child we are looking at. If
        # there is only one "found" child, then everything is OK.
        if len(found) == 1 and len(children) == 1:
            ch = children[0]
            pp = found[0]
            mm_p = datasets[pp]
            mm = dclab.new_dataset(mm_p)
            # Update configuration file
            item = index_dict[ch]
            cfgfile = join(tempdir, item["config"])
            cfg = Configuration(files=[cfgfile])
            cfg["filtering"]["hierarchy parent"] = mm_p.identifier
            cfg.save(cfgfile)
            mm.config.update(cfg)
            # Update index dictionary
            index_dict[ch]["parent hash"] = mm_p.hash
            index_dict[ch]["hash"] = mm.hash
            index_dict[ch]["parent key"] = pp
        else:
            # Note: If the user did not rename the titles of the hierarchy
            # children, then one might be able to infer the parents
            # of the deeper children from their titles.
            msg = "Opening old sessions with deep hierarchy not possible!"
            raise NotImplementedError(msg)

    index.index_save(tempdir, index_dict)


def search_hashed_measurement(mfile, index_item, directories, version):
    """Search for a data set using hashes
    
    Parameters
    ----------
    mfile: str
        The original path of the measurement file.
    index_item: dict
        Dictionary of this measurement file obtained from the
        index.txt file of a session (see `index` submodule).
    directories: list of str
        A list of directories to search recursively.
    version: distutils.version.LooseVersion
        The version of ShapeOut used to save the session
        (for backwards compatibility).
    
    Returns
    -------
    ffile: str or None
        Path to the found measurement file.
    
    Notes
    -----
    This method only searches for filenames that match the basename
    of the given `mfile`. 
    """
    mname = os.path.basename(mfile)
    for adir in directories:
        for root, _ds, fs in os.walk(adir):
            if mname in fs:
                this_file = os.path.join(root, mname)
                if version < LooseVersion("0.7.6"):
                    saved_hash = index_item["tdms hash"]
                    check_hash = hashfile_sha(this_file)
                    if saved_hash == check_hash:
                        return this_file
                else:
                    datahash = dclab.new_dataset(this_file).hash
                    if datahash == index_item["hash"]:
                        return this_file
