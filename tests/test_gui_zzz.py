#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This must be the last test executed for some unknown reason"""
from __future__ import division, print_function


def test_final():
    from shapeout.__main__ import prepare_app
    prepare_app()


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
