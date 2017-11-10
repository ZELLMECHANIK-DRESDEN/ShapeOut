#!/usr/bin/python
# -*- mode: python -*-
# find correct directory
import codecs
import os
from os.path import abspath, exists, join, dirname, relpath
import platform
import sys
import warnings

cdir = abspath(".")
sys.path.insert(0, cdir)

if not exists(join(cdir, "shapeout")):
	warnings.warn("Cannot find 'shapeout'! Please run pyinstaller "+
                  "from git root folder.")

name = "ShapeOut"
appdir = os.path.realpath(cdir+"/shapeout/")
pyinstdir = os.path.realpath(cdir+"/.appveyor/")
script = os.path.join(appdir, name+".py")

# Icon
icofile = os.path.join(pyinstdir,"ShapeOut.ico")

a = Analysis([script],
             pathex=[cdir],
             hookspath=[pyinstdir],
             runtime_hooks=None)
             
options = [ ('u', None, 'OPTION'), ('W ignore', None, 'OPTION') ]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name=name+".exe",
          debug=False,
          strip=False,
          upx=False,
          icon=icofile,
          console=False)

# things that are safe to remove and save space
remove_startswith = ["IPython", "libnvidia-glcore",
                     "libQtGui", "libQtWebKit",
                     "libQtXmlPatterns", "libQtCore", "qt4" ]
for mod in remove_startswith:
    a.binaries = [x for x in a.binaries if not x[0].startswith(mod)]


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name=name)
