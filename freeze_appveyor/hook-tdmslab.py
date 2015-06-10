import sys
import os

librtdcloc = os.path.realpath(os.path.dirname(__file__)+"../../../librtdc")
tdmslabloc = os.path.realpath(os.path.dirname(__file__)+"../../../librtdc/tdmslab")


#datas = []
## tdmslab files
datas = [(os.path.join(tdmslabloc,"tdmslab.cfg"), "tdmslab"),
         (os.path.join(tdmslabloc,"isoelastics"), "tdmslab")
            ]

hiddenimports = ["nptdms", "nptdms.version", "nptdms.tdms", "nptdms.tdmsinfo"]
hiddenimports += ["scipy.stats"]


## If these files don't exist, try to find tdms installation...
