#!/usr/bin/python
# -*- mode: python -*-
# find correct directory
import codecs
import os
from os.path import abspath, exists, join, dirname, relpath
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
artdir = os.path.realpath(dir+"/art/")
confdir = os.path.realpath(dir+"/config/")
datadir = os.path.realpath(dir+"/data/")
distdir = os.path.realpath(dir+"/dist/")
langdir = os.path.realpath(dir+"/lang/")
pyinstdir = os.path.realpath(dir+"/freeze_appveyor/")
script = os.path.join(appdir, name+".py")

# Icon
icofile = os.path.join(pyinstdir,"ShapeOut.ico")

# Add tag
# write repo tag name if possible (used by update)
tag_version = None
for var in ["APPVEYOR_REPO_TAG_NAME"]:
	val = os.getenv(var)
	if val is not None:
		tag_version = val
	break
if tag_version is not None:
	with open(join(appdir, "_version.py"), "a") as vfile:
		vfile.write('\nrepo_tag = "{}"\n'.format(tag_version))

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
nissfile = codecs.open("win_shapeout.iss", 'wb', "utf-8")
nissfile.write(u"\ufeff")
nissfile.writelines(iss)
nissfile.close()

## Hidden imports
# nptdms
hiddenimports = ["nptdms", "nptdms.version", "nptdms.tdms", "nptdms.tdmsinfo"]
# scipy stats
hiddenimports += ["scipy.stats", "scipy.special", "scipy.special._ufuncs_cxx"]
hiddenimports += ["dclab", "six"]


appdir = relpath(appdir,dir)
langdir = relpath(langdir,dir)


## Config files
datas = [
         (join(MEIrtdc,"dclab.cfg"),
          join(confdir, "dclab.cfg"),
          'DATA'),
         ]

## Data files
# recursively add isoelastics
isoeldir = join(datadir, "isoelastics")
MEIrtdcisoel = join(MEIrtdc, "isoelastics")
for root, _, files in os.walk(isoeldir):
    for f in files:
        reldir = os.path.relpath(root, isoeldir)
        datas += [
                  (join(join(MEIrtdcisoel, reldir), f),
                  join(join(isoeldir, reldir), f),
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
               strip=None,
               upx=True,
               name=name)
