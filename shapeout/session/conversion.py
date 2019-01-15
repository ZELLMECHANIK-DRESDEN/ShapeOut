#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - session conversion

Due to changes in naming conventions and refactoring in dclab,
the data stored in Shape-Out sessions depends on the the version
of dclab that was used at the time the session was saved.
Shape-Out releases come as Windows installers that contain a
specific version of dclab. Starting version 0.7.6, this
version is stored along with the session and it is used to
decide which parts of the session data needs conversion to
work with the current version of Shape-Out.
"""
from __future__ import division, print_function, unicode_literals

from distutils.version import LooseVersion
import hashlib
import os
import pathlib
import re
import sys
import tempfile

import numpy as np

import dclab
from dclab.rtdc_dataset.config import Configuration

from . import index

if sys.version_info[0] == 2:
    str_classes = (str, unicode)
else:
    str_classes = str


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
    """Case insensitive removal of a row contained in data

    Parameters
    ----------
    ident: str
        Lines starting with this string are removed
    """
    data = data.split("\n")
    newdata = []
    for ii in range(len(data)):
        if not data[ii].lower().startswith(ident.lower()):
            newdata.append(data[ii])
    return "\n".join(newdata)


def cleanup_old_config_sections(tempdir):
    """Remove old read-only config sections

    Remove read-only config.txt sections "framerate", "general",
    "roi", and "image".
    """
    tempdir = pathlib.Path(tempdir)
    index_dict = index.index_load(tempdir)
    for key in index_dict:
        cfgfile = tempdir / index_dict[key]["config"]
        cfg = Configuration(files=[cfgfile])
        for section in ["framerate",
                        "general",
                        "roi",
                        "image"
                        ]:
            if section in cfg:
                cfg._cfg.pop(section)
        cfg.save(cfgfile)


def compatibilitize_polygon(pdata, version=None):
    """Update polygon filters to latest format

    Parameters
    ----------
    pdata: list of str
        Data returned by `io.open(...).read()`
    version: None or `LooseVersion`
        The version string. If set to `None`, the version
        is inferred from the feature names in "x axis" and
        "y axis".

    Returns
    -------
    pdata_conv: list of str
        Corrected input data.
    """
    if version is None:
        # Try to guess version
        pre_076 = 0
        newc = [c[1] for c in compat_replace]
        for line in pdata.split("\n"):
            line = line.lower()
            if line.count("x axis =") or line.count("y axis ="):
                ax = line.split("=")[1].strip()
                if ax not in newc:
                    pre_076 += 1
        if pre_076:
            version = LooseVersion("0.0.1")
        else:
            version = LooseVersion("0.7.6")

    if version < LooseVersion("0.7.6"):
        for old, new in compat_replace:
            for pattern in ["\nx axis = {}\n",
                            "\ny axis = {}\n",
                            ]:
                pdata = ci_replace(pdata,
                                   pattern.format(old),
                                   pattern.format(new))
    return pdata


def compatibilitize_session(tempdir, hash_update=True, search_path="."):
    """Update extracted files to latest format

    Shape-Out 0.5.7
      - title saved in index.txt

    Shape-Out 0.7.1
      - change names of KDE accuracies
        (kde multivariate -> kde accuracy)

    Shape-Out 0.7.4
      - rewrite config.txt path to always use slash

    Shape-Out 0.7.5
      - remove emodulus computation parameters if accuracy not present

    Shape-Out 0.7.6
      - introduction of new feature names in dclab 0.2.5
      - all previous version did not support manual filters in
        hierarchy children (remove the _filter_manual.npy file)
      - update session hashes (if `hash_update` is set to `True`)

    Shape-Out 0.7.8
      - introduction of new key "identifier" in mm_dict
      - replace "parent id" key with "parent key" in hierarchy children

    Shape-Out 0.7.9
      - renamed feature "inert_ratio" to "inert_ratio_cvx"

    Shape-Out 0.8.1
      - removed read-only config.txt sections "framerate", "general",
        "roi", and "image".

    Shape-Out 0.8.4
      - change options for cfg["plotting"]["isoelastics"]
        previous: bool
        new: ["not shown", "analytical", "numerical", "legacy"]

    Shape-Out 0.8.6
      - remove configuration keys (dclab 0.3.4)
        [imaging]: "exposure time", "flash current"
        [setup]: "temperature", "viscosity"
        [online_contour]: "bin margin"
      - rename feature "ncells" to "nevents"


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
    tempdir = pathlib.Path(tempdir)
    search_path = pathlib.Path(search_path)
    version = index.index_version(tempdir)

    # Find all config.txt files and replace feature names
    change_configs = [f for f in tempdir.rglob("*config.txt")]

    # Add title to index
    if version < LooseVersion("0.5.7"):
        index_dict = index.index_load(tempdir)
        for key in index_dict:
            if "title" not in index_dict[key]:
                index_dict[key]["title"] = "no title"
        index.index_save(tempdir, index_dict)

    for cc in change_configs:
        with cc.open() as fd:
            data = fd.read()

        if version < LooseVersion("0.7.1"):
            data = ci_replace(data, "\nkde multivariate ", "\nkde accuracy ")

        if version < LooseVersion("0.7.5"):
            if data.count("kde accuracy emodulus") == 0:
                data = ci_rm_row(data, "emodulus medium = ")
                data = ci_rm_row(data, "emodulus model = ")
                data = ci_rm_row(data, "emodulus temperature = ")
                data = ci_rm_row(data, "emodulus viscosity = ")

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

        if version < LooseVersion("0.7.9"):
            old = "inert_ratio"
            new = "inert_ratio_cvx"
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

        if version < LooseVersion("0.8.4"):
            data = ci_replace(data,
                              "\nisoelastics = True\n",
                              "\nisoelastics = legacy\n")
            data = ci_replace(data,
                              "\nisoelastics = False\n",
                              "\nisoelastics = not shown\n")

        if version < LooseVersion("0.8.6"):
            # remove config keys
            data = ci_rm_row(data, "exposure time = ")
            data = ci_rm_row(data, "flash current = ")
            data = ci_rm_row(data, "temperature = ")
            data = ci_rm_row(data, "viscosity = ")
            data = ci_rm_row(data, "bin margin = ")
            # rename feature
            old = "ncells"
            new = "nevents"
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

        with cc.open("w") as fd:
            fd.write(data)

    # Change polygon filters as well
    pfile = tempdir / "PolygonFilters.poly"
    if pfile.exists():
        with pfile.open() as fd:
            datap = fd.read()

        if version < LooseVersion("0.7.6"):
            datap = compatibilitize_polygon(pdata=datap,
                                            version=version)

        with pfile.open("w") as fd:
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
                filtman = tempdir / key / "_filter_manual.npy"
                if filtman.exists():
                    filtman.unlink()

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

    # Cleanup redundant read-only configuration sections
    if version < LooseVersion("0.8.1"):
        cleanup_old_config_sections(tempdir)

    return version


def convert_polygon(infile, outfile=None, version=None):
    """Convert a polygon filter file

    Parameters
    ----------
    infile: path to .poly file
        The input filename.
    outfile: path to .poly file or `None`
        The ouptut filename. If set to `None`, a temporary
        file will be created.
    version: None or `LooseVersion`
        The version string. If set to `None`, the version
        is inferred from the feature names in "x axis" and
        "y axis".

    Returns
    -------
    outfile: path to output .poly file
    """
    infile = pathlib.Path(infile)
    if outfile is None:
        _fd, outfile = tempfile.mkstemp(prefix="converted_filter_",
                                        suffix=".poly")
    outfile = pathlib.Path(outfile)

    with infile.open() as fd:
        pdata = fd.read()
    pdata = compatibilitize_polygon(pdata=pdata, version=version)

    with outfile.open("w") as fd:
        fd.write(pdata)

    return outfile


def hashfile_sha(fname, blocksize=65536):
    """Compute sha256 hex-hash of a file

    Parameters
    ----------
    fname: str
        path to the file
    blocksize: int
        block size read from the file
    """
    fname = pathlib.Path(fname)
    hasher = hashlib.sha256()
    with fname.open('rb') as fd:
        buf = fd.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fd.read(blocksize)
    return hasher.hexdigest()


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
    else:
        raise ValueError("No rule to convert object '{}' to string.".
                         format(obj.__class__))


def old_tdms_saved_hash(index_item):
    """Compute md5 hash from data stored in old session index"""
    if "fdir_orig" in index_item:
        # Use the original directory name for hashing
        fd = index_item["fdir_orig"]
    else:
        fd = index_item["fdir"]

    ff = index_item["name"]

    if fd.count(":\\"):
        tdms_path = fd + "\\" + ff
        mx = fd + "\\" + ff.split("_")[0]
    else:
        tdms_path = fd + "/" + ff
        mx = fd + "/" + ff.split("_")[0]

    file_hashes = [(tdms_path, index_item["tdms hash"]),
                   (mx+"_camera.ini", index_item["camera.ini hash"]),
                   (mx+"_para.ini", index_item["para.ini hash"])
                   ]

    ihasher = hashlib.md5()
    ihasher.update(obj2str(tdms_path))
    ihasher.update(obj2str(file_hashes))
    return ihasher.hexdigest()


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
        The version of Shape-Out used to save the session
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
    mfile = pathlib.Path(mfile)
    for adir in directories:
        for root, _ds, fs in os.walk(str(adir)):
            root = pathlib.Path(root)
            if mfile.name in fs:
                this_file = root / mfile.name
                if version < LooseVersion("0.7.6"):
                    saved_hash = index_item["tdms hash"]
                    check_hash = hashfile_sha(this_file)
                    if saved_hash == check_hash:
                        return this_file
                else:
                    datahash = dclab.new_dataset(this_file).hash
                    if datahash == index_item["hash"]:
                        return this_file


def update_session_hashes(tempdir, search_path="."):
    """Find all hierarchy children and compute correct hash

    - Replace old hashes with new hashes
    - Fix some (not all) hierarchy problems

    New hashing methods were introduced in Shape-Out 0.7.6.
    Do not call this method for later sessions.

    This method assumes that the paths to the measurement files
    are correct. It is therefore not included in the
    `compatibilitize_session` method.
    """
    tempdir = pathlib.Path(tempdir)
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
        cfgfile = tempdir / item["config"]
        cfg = Configuration(files=[cfgfile])
        mm = dclab.new_dataset(path)
        mm.config.update(cfg)
        mm.apply_filter()
        datasets[pp] = mm
        # record parent hashes
        hashes[pp] = [old, mm.hash]

        index_dict[pp].pop("tdms hash")
        index_dict[pp].pop("camera.ini hash")
        index_dict[pp].pop("para.ini hash")
        index_dict[pp]["hash"] = mm.hash
        index_dict[pp]["fdir"] = path.parent

    # As long as there are children, iteratively search
    # for their parents.
    found = []
    for ch in children:
        item = index_dict[ch]
        # Get configuration of child
        cfgfile = tempdir / item["config"]
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
        # Shape-Out, the parent of a children was identified
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
            cfgfile = tempdir / item["config"]
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
