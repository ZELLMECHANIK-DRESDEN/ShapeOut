#-----------------------------------------------------------------------------
# Copyright (c) 2017, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

# Hook for ShapeOut: https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut

from PyInstaller.utils.hooks import collect_data_files

# Data files
datas = collect_data_files("shapeout")
datas += collect_data_files("shapeout", subdir="img")
datas += collect_data_files("shapeout", subdir="cfg")
datas += collect_data_files("shapeout", subdir="data")


## Hidden imports
# nptdms
hiddenimports = ["nptdms", "nptdms.version", "nptdms.tdms", "nptdms.tdmsinfo",
                 "pathlib"]
# scipy stats
hiddenimports += ["scipy.stats", "scipy.special", "scipy.special._ufuncs_cxx"]
hiddenimports += ["dclab", "six"]
