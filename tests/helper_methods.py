import os
import os.path as op
import pathlib
import shutil
import tempfile
import zipfile

import numpy as np

from shapeout.meta_tool import find_data

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
            state = np.random.RandomState(size + ii)
            val = state.random_sample(size)
        ddict[key] = val

    return ddict


def extract_session(name):
    global _tempdirs
    path = retrieve_session(name)
    Arc = zipfile.ZipFile(path, mode='r')
    tempdir = tempfile.mkdtemp(prefix="ShapeOut-test_")
    Arc.extractall(tempdir)
    Arc.close()
    _tempdirs.append(tempdir)
    return tempdir, op.dirname(path)


def retrieve_data(zip_file):
    """Eytract contents of data zip file and return dir
    """
    global _tempdirs
    zpath = pathlib.Path(__file__).resolve().parent / "data" / zip_file
    # unpack
    arc = zipfile.ZipFile(str(zpath))

    # extract all files to a temporary directory
    edest = tempfile.mkdtemp(prefix=zpath.name)
    arc.extractall(edest)

    _tempdirs.append(edest)

    # Load RT-DC Data set
    # find hdf5/tdms files
    datafiles = find_data(edest)

    if len(datafiles) == 1:
        datafiles = datafiles[0]

    return datafiles


def retrieve_session(zmso_file):
    """Return path to session file with data in same dir"""
    global _tempdirs
    ddir = pathlib.Path(__file__).resolve().parent / "data"
    zpath = ddir / zmso_file

    # extract all files to a temporary directory
    edest = pathlib.Path(tempfile.mkdtemp(prefix=zpath.name))
    _tempdirs.append(str(edest))

    # unpack ALL data files (might result in overhead)
    for ed in example_data_sets:
        arc = zipfile.ZipFile(str(ddir / ed))
        mdir = str(edest / ed[:-4])
        os.mkdir(mdir)
        arc.extractall(mdir)

    # copy session file
    shutil.copy2(str(zpath), str(edest))
    return str(edest / zpath.name)


# Do not change order
example_data_sets = ["rtdc_data_minimal.zip",
                     "rtdc_data_traces_video.zip",
                     "rtdc_data_hdf5_contour_image_trace.zip"]

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
