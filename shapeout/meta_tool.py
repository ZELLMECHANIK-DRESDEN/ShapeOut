#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - meta data functionalities"""
from __future__ import division, unicode_literals

import hashlib
import pathlib
import warnings

import h5py
import imageio
import nptdms

from dclab.rtdc_dataset import config as rt_config
from dclab.rtdc_dataset import fmt_tdms

from .util import path_to_str

from . import settings


def collect_data_tree(directories):
    """Return projects (folders) and measurements therein

    This is a convenience function for the GUI
    """
    if not isinstance(directories, list):
        directories = [directories]

    directories = list(set(directories))

    pathdict = {}
    treelist = []

    for directory in directories:
        files = find_data(directory)

        cols = ["Measurement"]

        for ff in files:
            if not verify_dataset(ff):
                # Ignore broken measurements
                continue
            path = path_to_str(ff.parent)
            # try to find the path in pathdict
            if pathdict.has_key(path):
                dirindex = pathdict[path]
            else:
                treelist.append([])
                dirindex = len(treelist) - 1
                pathdict[path] = dirindex
                # The first element of a tree contains the measurement name
                project = get_sample_name(ff)
                treelist[dirindex].append((project, path))
            # Get data from filename
            mx = get_run_index(ff)
            chip_region = get_chip_region(ff)
            dn = u"M{} {}".format(mx, chip_region)
            if not chip_region.lower() in ["reservoir"]:
                # outlet (flow rate is not important)
                dn += u"  {:.5f} µls⁻¹".format(get_flow_rate(ff))
            dn += "  ({} events)".format(get_event_count(ff))

            treelist[dirindex].append((dn, path_to_str(ff)))

    return treelist, cols


def find_data(path):
    """Find tdms and rtdc data files in a directory"""
    path = pathlib.Path(path)

    def sort_path(path):
        """Sorting key for intuitive file sorting

        This sorts a list of RT-DC files according to measurement number,
        e.g. (M2_*.tdms is not sorted after M11_*.tdms):

        /path/to/M1_*.tdms
        /path/to/M2_*.tdms
        /path/to/M10_*.tdms
        /path/to/M11_*.tdms

        Note that the measurement number of .rtdc files is extracted from
        the hdf5 metadata and not from the file name.
        """
        try:
            # try to get measurement number as an integer
            idx = get_run_index(path)
        except BaseException:
            # just use the given path
            name = path.name
        else:
            # assign new "name" for sorting
            name = "{:09d}_{}".format(idx, path.name)
        return path.with_name(name)

    tdmsfiles = fmt_tdms.get_tdms_files(path)
    tdmsfiles = sorted(tdmsfiles, key=sort_path)
    rtdcfiles = [r for r in path.rglob("*.rtdc") if r.is_file()]
    rtdcfiles = sorted(rtdcfiles, key=sort_path)

    files = [pathlib.Path(ff) for ff in rtdcfiles + tdmsfiles]
    return files


def get_event_count(fname):
    """Get the number of events in a data set

    Parameters
    ----------
    fname: str
        Path to an experimental data file. The file format is
        determined from the file extension (tdms or rtdc).

    Returns
    -------
    event_count: int
        The number of events in the data set

    Notes
    -----
    For tdms-based data sets, there are multiple ways of determining
    the number of events, which are used in the following order
    (according to which is faster):
    1. The MX_log.ini file "Events" tag
    2. The number of frames in the avi file
    3. The tdms file (very slow, because it loads the entire tdms file)
       The values obtained with this method are cached on disk to
       speed up future calls with the same argument.

    See Also
    --------
    get_event_count_cache: cached event counts from tdms/avi files
    """
    fname = pathlib.Path(fname).resolve()
    ext = fname.suffix

    if ext == ".rtdc":
        with h5py.File(path_to_str(fname), mode="r") as h5:
            event_count = h5.attrs["experiment:event count"]
    elif ext == ".tdms":
        mdir = fname.parent
        mid = fname.name.split("_")[0]
        # possible data sources
        logf = mdir / (mid + "_log.ini")
        avif = mdir / (mid + "_imaq.avi")
        if logf.exists():
            # 1. The MX_log.ini file "Events" tag
            with logf.open() as fd:
                logd = fd.readlines()
            for l in logd:
                if l.strip().startswith("Events:"):
                    event_count = int(l.split(":")[1])
                    break
        elif avif.exists():
            # 2. The number of frames in the avi file
            event_count = get_event_count_cache(avif)
        else:
            # 3. Open the tdms file
            event_count = get_event_count_cache(fname)
    else:
        raise ValueError("`fname` must be an .rtdc or .tdms file!")

    return event_count


def get_event_count_cache(fname):
    """Get the number of events from a tdms or avi file

    Parameters
    ----------
    fname: str
        Path to an experimental data file (tdms or avi)

    Returns
    -------
    event_count: int
        The number of events in the data set

    Notes
    -----
    The values for a file name are cached on disk using
    the file name and the first 100kB of the file as a
    key.
    """
    fname = pathlib.Path(fname).resolve()
    ext = fname.suffix
    # Generate key
    with fname.open(mode="rb") as fd:
        data = fd.read(100 * 1024)
    strfname = str(fname).encode("zip")
    fhash = hashlib.md5(data + strfname).hexdigest()
    cfgec = settings.SettingsFileCache(name="shapeout_tdms_event_counts.txt")
    try:
        event_count = cfgec.get_int(fhash)
    except KeyError:
        if ext == ".avi":
            with imageio.get_reader(fname) as video:
                event_count = len(video)
        elif ext == ".tdms":
            tdmsfd = nptdms.TdmsFile(path_to_str(fname))
            event_count = len(tdmsfd.object("Cell Track", "time").data)
        else:
            raise ValueError("unsupported file extension: {}".format(ext))
        cfgec.set_int(fhash, event_count)
    return event_count


def get_flow_rate(fname):
    """Get the flow rate of a data set

    Parameters
    ----------
    fname: str
        Path to an experimental data file. The file format is
        determined from the file extenssion (tdms or rtdc).

    Returns
    -------
    flow_rate: float
        The flow rate [µL/s] of the data set
    """
    fname = pathlib.Path(fname).resolve()
    ext = fname.suffix

    if ext == ".rtdc":
        with h5py.File(path_to_str(fname), mode="r") as h5:
            flow_rate = h5.attrs["setup:flow rate"]
    elif ext == ".tdms":
        name = fname.name
        path = fname.parent
        mx = name.split("_")[0]
        para = path / (mx + "_para.ini")
        if para.exists():
            camcfg = rt_config.load_from_file(path_to_str(para))
            flow_rate = camcfg["general"]["flow rate [ul/s]"]
        else:
            # analyze the filename
            warnings.warn("{}: trying to manually find flow rate.".
                          format(fname))
            flow_rate = float(fname.split("ul_s")[0].split("_")[-1])
    else:
        raise ValueError("`fname` must be an .rtdc or .tdms file!")

    return flow_rate


def get_chip_region(fname):
    """Get the chip region of a data set

    Parameters
    ----------
    fname: str
        Path to an experimental data file. The file format is
        determined from the file extenssion (tdms or rtdc).

    Returns
    -------
    chip_region: str
        The chip region ("channel" or "reservoir")
    """
    fname = pathlib.Path(fname).resolve()
    ext = fname.suffix

    if ext == ".rtdc":
        with h5py.File(path_to_str(fname), mode="r") as h5:
            chip_region = h5.attrs["setup:chip region"]
    elif ext == ".tdms":
        name = fname.name
        path = fname.parent
        mx = name.split("_")[0]
        para = path / (mx + "_para.ini")
        if para.exists():
            camcfg = rt_config.load_from_file(path_to_str(para))
            chip_region = camcfg["General"]["Region"].lower()

    return chip_region


def get_run_index(fname):
    fname = pathlib.Path(fname).resolve()
    ext = fname.suffix
    if ext == ".rtdc":
        with h5py.File(path_to_str(fname), mode="r") as h5:
            run_index = h5.attrs["experiment:run index"]
    elif ext == ".tdms":
        name = fname.name
        run_index = int(name.split("_")[0].strip("Mm "))
    return run_index


def get_sample_name(fname):
    fname = pathlib.Path(fname).resolve()
    ext = fname.suffix
    if ext == ".rtdc":
        with h5py.File(path_to_str(fname), mode="r") as h5:
            sample = h5.attrs["experiment:sample"]
    elif ext == ".tdms":
        sample = fmt_tdms.get_project_name_from_path(fname)
    return sample


def verify_dataset(path, verbose=False):
    """Returns `True` if the data set is complete/usable"""
    path = pathlib.Path(path).resolve()
    if path.suffix == ".tdms":
        is_ok = True
        parent = path.parent
        name = path.name
        mx = name.split("_")[0]

        # Check if all config files are present
        if ((not (parent / (mx + "_para.ini")).exists()) or
                    (not (parent / (mx + "_camera.ini")).exists()) or
                    (not path.exists())
                ):
            if verbose:
                print("config files missing")
            is_ok = False

        # Check if we can perform all standard file operations
        for test in [get_chip_region, get_flow_rate, get_event_count]:
            try:
                test(path)
            except:
                if verbose:
                    print("standard file operations failed")
                is_ok = False
                break
    elif path.suffix == ".rtdc":
        try:
            with h5py.File(path_to_str(path), mode="r") as h5:
                for key in ["experiment:event count",
                            "experiment:sample",
                            "experiment:run index",
                            "imaging:pixel size",
                            "setup:channel width",
                            "setup:chip region",
                            "setup:flow rate",
                            ]:
                    if key not in h5.attrs:
                        if verbose:
                            print("fmt_rtdc keys missing")
                        is_ok = False
                        break
                else:
                    is_ok = True
        except IOError:
            if verbose:
                print("data file broken")
            is_ok = False
    else:
        if verbose:
            print("unsupported format")
        is_ok = False

    return is_ok
