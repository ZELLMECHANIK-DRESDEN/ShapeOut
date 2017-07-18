import os
from os.path import join, basename, dirname, abspath
import shutil
import sys
import tempfile
import zipfile

import numpy as np


sys.path.insert(0, dirname(dirname(abspath(__file__))))

from dclab.rtdc_dataset.fmt_tdms import get_tdms_files

_tempdirs = []


def cleanup():
    """Removes all extracted directories"""
    global _tempdirs
    for _i in range(len(_tempdirs)):
        tdir = _tempdirs.pop(0)
        shutil.rmtree(tdir, ignore_errors=True)


def example_data_dict(size=100, keys=["area_um", "deform"]):
    """Example dict with which an RT-DC dataset can be instantiated.
    """
    ddict = {}
    for ii, key in enumerate(keys):
        if key in ["time", "frame"]:
            val = np.arange(size)
        else:
            state = np.random.RandomState(size+ii)
            val = state.random_sample(size)
        ddict[key] = val
    
    return ddict


def retreive_tdms(zip_file):
    """ Retrieve a zip file that is reachable via the location
    `webloc`, extract it, and return the paths to extracted
    tdms files.
    """
    global _tempdirs
    thisdir = dirname(abspath(__file__))
    ddir = join(thisdir, "data")
    # unpack
    arc = zipfile.ZipFile(join(ddir, zip_file))
    
    # extract all files to a temporary directory
    edest = tempfile.mkdtemp(prefix=basename(zip_file))
    arc.extractall(edest)
    
    _tempdirs.append(edest)
    
    ## Load RTDC Data set
    # find tdms files
    tdmsfiles = get_tdms_files(edest)
    
    if len(tdmsfiles) == 1:
        tdmsfiles = tdmsfiles[0]

    return tdmsfiles


def retreive_session(zsmo_file):
    """Return path to session file with data in same dir"""
    global _tempdirs
    thisdir = dirname(abspath(__file__))
    ddir = join(thisdir, "data")

    # extract all files to a temporary directory
    edest = tempfile.mkdtemp(prefix=basename(zsmo_file))
    _tempdirs.append(edest)

    # unpack ALL data files (might result in overhead)
    for ed in example_data_sets:
        arc = zipfile.ZipFile(join(ddir, ed))
        mdir = join(edest, ed[:-4])
        os.mkdir(mdir)
        arc.extractall(mdir)
    
    # copy session file
    shutil.copy2(join(ddir, zsmo_file), edest)
    return join(edest, zsmo_file)


    
# Do not change order    
example_data_sets = ["rtdc_data_minimal.zip",
                     "rtdc_data_traces_video.zip"]

example_sessions = ["session_v0.6.0.zmso",
                    "session_v0.6.5.zmso",
                    "session_v0.7.0.zmso",
                    "session_v0.7.0_hierarchy2.zmso",
                    "session_v0.7.4_hierarchy2.zmso",
                    "session_v0.7.5_hierarchy1.zmso",
                    "session_v0.7.5_hierarchy2.zmso",
                    "session_v0.7.6_hierarchy2.zmso",
                    "session_v0.7.7_hierarchy2.zmso",
                    ]
