#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import dirname, realpath, exists
from setuptools import setup, find_packages
import sys


author = u"Paul Müller"
authors = [author, u"Philipp Rosendahl", u"Maik Herbig"]
name = 'shapeout'
description = 'User interface for real-time deformability cytometry (RT-DC)'
year = "2015"


sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
from _version import version

setup(
    name=name,
    author=author,
    author_email='dev@craban.de',
    url='https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="GPL v2",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    extras_require = {# Graphical User Interface
                      # If you need the GUI for your project, add
                      # "shapeout[GUI]" to your install_requires.
                      'GUI':  ["chaco",
                               "simplejson",  # for updates
                               "wxPython>=3.0.0,<4.0.0",
                               # these are additional dependencies of chaco
                               "kiwisolver",
                               "reportlab",
                               ],
                      },
    install_requires=["appdirs",
                      "dclab>=0.10.2",
                      "fcswrite>=0.4.1",
                      "h5py>=2.8.0",
                      "imageio>=2.3.0,<2.5.0",
                      "nptdms",
                      # numpy>=1.13 is not compatible with chaco
                      # (ValueError when testing with an array)
                      "numpy>=1.9.0,<1.13.0",
                      "pathlib",
                      "pyper",
                      "scipy>=0.13.0",
                      ],
    setup_requires=['pytest-runner'],
    tests_require=["pytest", "urllib3"],
    keywords=["RT-DC", "deformability", "cytometry", "zellmechanik"],
    classifiers= ['Operating System :: OS Independent',
                  'Programming Language :: Python :: 2.7',
                  'Intended Audience :: Science/Research',
                  ],
    platforms=['ALL']
    )
