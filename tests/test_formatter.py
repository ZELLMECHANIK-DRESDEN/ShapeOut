#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test correct string formatting.
"""
from __future__ import division, print_function

import numpy as np

from shapeout.util import float2string_nsf


def test_string_formatter():
    a = 1.23456789
    b = a * 10.**(np.arange(-10, 10))
    n = 4

    results = []

    for fval in b:
        results.append(float2string_nsf(fval, n=n))

    shouldbe = ["0.00000000012346",
                "0.0000000012346",
                "0.000000012346",
                "0.00000012346",
                "0.0000012346",
                "0.000012346",
                "0.00012346",
                "0.0012346",
                "0.012346",
                "0.12346",
                "1.2346",
                "12.346",
                "123.46",
                "1234.6",
                "12346",
                "123457",
                "1234568",
                "12345679",
                "123456789",
                "1234567890", ]

    for ii in range(len(b)):
        assert shouldbe[ii] == results[ii]


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
