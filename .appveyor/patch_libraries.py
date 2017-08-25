#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Patch libraries that cause trouble during freezing.
Must be run with administrative rights.

"""
from __future__ import print_function



def patch_pyface():
    """
    fix bug: 
    
    raise NotImplementedError("the %s pyface backend doesn't implement %s" % (ETSConfig.toolkit, oname))
    
    """
    
    print("Patching pyface...")
    import pyface
    import pyface.toolkit

    fname = pyface.toolkit.__file__[:-1] # strip "c" of pyc

    #read file:
    with open(fname, "r") as f:
        data=f.readlines()

    # go through data and edit
    cout = "raise NotImplementedError"
    for i, d in enumerate(data):
        count=0
        if d.strip().startswith(cout):
            indent=len(d)-len(d.lstrip(" "))
            data[i+count] = ("#"+d).strip()+"#ShapeOut patch\n"
            data.insert(i+1+count, indent*" "+"pass #ShapeOut patch\n")
            count += 1

    with open(fname, "w") as f:
        f.writelines(data)


if __name__ == "__main__":
    patch_pyface()
