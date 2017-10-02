#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ShapeOut - meta data functionalities"""
from __future__ import division, unicode_literals

import hashlib
import io
import os
import os.path as op
import warnings

import h5py
import imageio
import nptdms

from dclab.rtdc_dataset import config as rt_config

from . import configuration


def get_event_count(fname):
    """Get the number of events in a data set
    
    Parameters
    ----------
    fname: str
        Path to an experimental data file. The file format is
        determined from the file extenssion (tdms or rtdc).
    
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
    get_event_count_tdms_cache: 
    """
    fname = op.abspath(fname)
    ext = op.splitext(fname)[1]
    
    if ext == ".rtdc":
        with h5py.File(fname) as fd:
            event_count = fd["meta"]["experiment"]["event count"]
    elif ext == ".tdms":
        mdir = op.dirname(fname)
        mid = op.basename(fname).split("_")[0]
        # possible data sources
        logf = op.join(mdir, mid+"_log.ini")
        avif = op.join(mdir, mid+"_imaq.avi")
        if op.exists(logf):
            # 1. The MX_log.ini file "Events" tag
            with open(logf) as fd:
                logd = fd.readlines()
            for l in logd:
                if l.strip().startswith("Events:"):
                    event_count = int(l.split(":")[1])
                    break
        elif os.path.exists(avif):
            # 2. The number of frames in the avi file
            event_count = get_event_count_cache(fname)
        else:
            # 3. Open the tdms file
            event_count = get_event_count_cache(fname)
    else:
        raise ValueError("`fname` must be an .rtdc or .tdms file!")
    
    return event_count


def get_event_count_cache(fname):
    """Get the number of events in a tdms file
    
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
    fname = op.abspath(fname)
    ext = op.splitext(fname)[1]
    # Generate key
    with io.open(fname, "rb") as fd:
        data = fd.read(100 * 1024)
    fhash = hashlib.md5(data + fname.encode("utf-8")).hexdigest()
    cfgec = configuration.ConfigurationFile(
                                name="shapeout_tdms_event_counts.txt",
                                defaults={},
                                datatype="cache")
    try:
        event_count = cfgec.get_int(fhash)
    except KeyError:
        if ext == ".avi":
            video = imageio.get_reader(fname)
            event_count = len(video)
        elif ext == ".tdms":
            tdmsfd = nptdms.TdmsFile(fname)
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
    fname = op.abspath(fname)
    ext = op.splitext(fname)[1]
    
    if ext == ".rtdc":
        with h5py.File(fname) as fd:
            flow_rate = fd["meta"]["setup"]["flow rate"]
    elif ext == ".tdms":
        path, name = op.split(fname)
        mx = name.split("_")[0]
        stem = os.path.join(path, mx)
        if op.exists(stem+"_para.ini"):
            camcfg = rt_config.load_from_file(stem+"_para.ini")
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
    fname = op.abspath(fname)
    ext = op.splitext(fname)[1]
    
    if ext == ".rtdc":
        with h5py.File(fname) as fd:
            chip_region = fd["meta"]["setup"]["chip region"]
    elif ext == ".tdms":
        path, name = op.split(fname)
        mx = name.split("_")[0]
        stem = os.path.join(path, mx)
        if op.exists(stem+"_para.ini"):
            camcfg = rt_config.load_from_file(stem+"_para.ini")
            chip_region = camcfg["General"]["Region"].lower()

    return chip_region
