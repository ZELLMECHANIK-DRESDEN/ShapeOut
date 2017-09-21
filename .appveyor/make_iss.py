# Create inno setup .iss file
from __future__ import unicode_literals
import io
import os
import os.path as op
import platform
import sys

# make library available
cdir = op.dirname(op.abspath(__file__))
pdir = op.dirname(cdir)
sys.path.insert(0, pdir)

# get version
import shapeout
version = shapeout.__version__

# read dummy
with io.open(op.join(cdir, "shapeout.iss_dummy"), 'r') as dummy:
    iss = dummy.readlines()

# replace keywords
for i in range(len(iss)):
    if iss[i].strip().startswith("#define MyAppVersion"):
        iss[i] = '#define MyAppVersion "{:s}"\n'.format(version)
    if iss[i].strip().startswith("#define MyAppPlatform"):
        # sys.maxint returns the same for windows 64bit verions
        iss[i] = '#define MyAppPlatform "win_{}"\n'.format(platform.architecture()[0])

# write iss
with io.open(op.join(cdir, "shapeout.iss"), 'w') as issfile:
    issfile.writelines(iss)

