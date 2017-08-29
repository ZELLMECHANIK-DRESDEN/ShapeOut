#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import dirname, realpath, exists
from setuptools import setup, find_packages
import sys


author = u"Paul Müller"
authors = [author, u"Philipp Rosendahl", u"Maik Herbig"]
name = 'shapeout'
description = 'Data analysis for real-time deformability cytometry (RTDC)'
year = "2015"


sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
try:
    from _version import version
except:
    version = "unknown"



if __name__ == "__main__":
    setup(
        name=name,
        author=author,
        author_email='paul.mueller@biotec.tu-dresden.de',
        url='https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut',
        version=version,
        packages=find_packages(include=(name+"*",)),
        package_dir={name: name},
        license="GPL v2",
        description=description,
        long_description=open('README.rst').read() if exists('README.rst') else '',
        extras_require = {
            # Graphical User Interface
            # If you need the GUI for your project, add
            # "shapeout[GUI]" to your install_requires.
            'GUI':  ["wxPython",
                     "chaco",
                     "imageio",
                     "simplejson", # for updates
                     ],
        },
        install_requires=["appdirs",
                          "dclab",
                          "NumPy>=1.7.0",
                          "SciPy>=0.13.0",
                          "pyper"],
        setup_requires=['pytest-runner'],
        tests_require=["pytest", "urllib3"],
        keywords=["RT-DC", "cytometry"],
        classifiers= [
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2.7',
            'Intended Audience :: Science/Research'
                     ],
        platforms=['ALL']
        )
