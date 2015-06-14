#!/usr/bin/python
# -*- mode: python -*-
# find correct directory
import codecs
import os
from os.path import abspath, exists, join, dirname 
import platform
import sys
import warnings

dir = abspath(".")

if not exists(join(dir, "shapeout")):
	warnings.warn("Cannot find 'shapeout'! Please run pyinstaller "+
                  "from git root folder.")


MEIrtdc="shapeout-data"
name = "ShapeOut"
appdir = os.path.realpath(dir+"/shapeout/")
confdir = os.path.realpath(dir+"/config/")
datadir = os.path.realpath(dir+"/data/")
distdir = os.path.realpath(dir+"/dist/")
langdir = os.path.realpath(dir+"/lang/")
artdir = os.path.realpath(dir+"/art/")
pyinstdir = os.path.realpath(dir+"/freeze_appveyor/")
script = os.path.join(appdir, name+".py")

## Create inno setup .iss file
sys.path.insert(0, appdir)
from _version import version
issfile = codecs.open(os.path.join(pyinstdir,"win_shapeout.iss"), 'r', "utf-8")
iss = issfile.readlines()
issfile.close()

for i in range(len(iss)):
    if iss[i].strip().startswith("#define MyAppVersion"):
        iss[i] = '#define MyAppVersion "{:s}"\n'.format(version)
    if iss[i].strip().startswith("#define MyAppPlatform"):
        # sys.maxint returns the same for windows 64bit verions
        iss[i] = '#define MyAppPlatform "win_{}"\n'.format(platform.architecture()[0])
nissfile = codecs.open("win7_innosetup.iss", 'wb', "utf-8")
nissfile.write(u"\ufeff")
nissfile.writelines(iss)
nissfile.close()

## Hidden imports
# nptdms
hiddenimports = ["nptdms", "nptdms.version", "nptdms.tdms", "nptdms.tdmsinfo"]
# scipy stats
hiddenimports += ["scipy.stats", "scipy.special", "scipy.special._ufuncs_cxx"]
hiddenimports += ["dclab", "six"]


appdir = os.path.relpath(appdir,dir)
langdir = os.path.relpath(langdir,dir)


## Data files
datas = [
         (os.path.join(MEIrtdc,"dclab.cfg"),
          os.path.join(confdir, "dclab.cfg"),
          'DATA'),
         ]


## Language files
for root,dirs,files in os.walk(langdir):
    for f in files:
        if os.path.splitext(f)[1] in [".ini", ".mo"]:
            datas += [(
                       os.path.join(MEIrtdc+"/lang",
                        os.path.relpath(os.path.join(root,f), langdir)),
                       os.path.relpath(os.path.join(root,f), dir),
                       "DATA"
                      )]


## Artwork
for root,dirs,files in os.walk(artdir):
    for f in files:
        if os.path.splitext(f)[1] in [".png"]:
            datas += [(
                       os.path.join(MEIrtdc+"/art",
                        os.path.relpath(os.path.join(root,f), artdir)),
                       os.path.relpath(os.path.join(root,f), dir),
                       "DATA"
                      )]



a = Analysis([script],
             pathex=[dir],
             hiddenimports=hiddenimports,
             hookspath=[pyinstdir],
             runtime_hooks=None)

             
a.datas += datas
             
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=name+".exe",
          debug=False,
          strip=None,
          upx=True,
          console=False)

# things that are safe to remove and save space
remove_startswith = ["IPython", "_ssl", "libssl",
                     "libcrypto", "libnvidia-glcore",
                     "libQtGui", "libQtWebKit",
                     "libQtXmlPatterns", "libQtCore", "qt4" ]
for mod in remove_startswith:
    a.binaries = [x for x in a.binaries if not x[0].startswith(mod)]


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=name)
