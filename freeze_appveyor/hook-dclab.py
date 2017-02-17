from pkg_resources import resource_filename  # @UnresolvedImport

import dclab
cfgfile = resource_filename("dclab", 'dclab.cfg')
cfgfile2 = resource_filename("dclab.rtdc_dataset", 'config_default.cfg')

## dclab files
datas = [(cfgfile, "dclab")]
datas += [(cfgfile2, "dclab/rtdc_dataset")]

hiddenimports = ["nptdms", "nptdms.version", "nptdms.tdms", "nptdms.tdmsinfo"]
hiddenimports += ["scipy.stats"]
