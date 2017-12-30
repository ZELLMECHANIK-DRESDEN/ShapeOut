#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import pathlib

from shapeout import configuration


def test_cfg_basic():
    cfg = configuration.ConfigurationFile()
    wd = pathlib.Path(".").resolve()
    cfg.set_dir(str(wd.parent), "Peter")

    assert wd.parent == pathlib.Path(cfg.get_dir("Peter")).resolve()


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
