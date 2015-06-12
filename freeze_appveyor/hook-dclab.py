import os
from pkg_resources import resource_filename  # @UnresolvedImport

import dclab
cfgfile = resource_filename("dclab", 'dclab.cfg')

## dclab files
datas = [(cfgfile, "dclab")]

hiddenimports = ["nptdms", "nptdms.version", "nptdms.tdms", "nptdms.tdmsinfo"]
hiddenimports += ["scipy.stats"]
