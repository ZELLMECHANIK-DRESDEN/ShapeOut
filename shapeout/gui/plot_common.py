#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Common plotting methods"""
from __future__ import print_function, division, unicode_literals

import os
from pkg_resources import resource_filename
import warnings

import chaco
import numpy as np

from dclab import isoelastics


class MyTickGenerator(chaco.ticks.AbstractTickGenerator):
    """ An implementation of AbstractTickGenerator that simply uses the
    auto_ticks() and log_auto_ticks() functions.
    """
    def get_ticks(self, data_low, data_high, bounds_low,
                  bounds_high, interval, use_endpoints=False,
                  scale='linear'):
        if scale == 'linear':
            return np.array(chaco.ticks.auto_ticks(data_low, data_high, bounds_low, bounds_high,
                         interval, use_endpoints=False), np.float64)
        elif scale == 'log':
            return np.array(my_log_auto_ticks(data_low, data_high, bounds_low, bounds_high,
                                              interval, use_endpoints=False), np.float64)


def get_isoelastics(mm):
    isotype = mm.config["plotting"]["isoelastics"]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()
    if isotype == "not shown":
        # nothing to do
        isoel = None
    else:
        if "legacy" in isotype:
            method = "analytical"
            isosource = legacy_isoelastics
            add_px_err = False
            px_um = None
        else:
            method = isotype
            isosource = isoelastics.get_default()
            add_px_err = True
            px_um = mm.config["imaging"]["pixel size"]
        kwargs = dict(method=method,
                      channel_width=mm.config["setup"]["channel width"],
                      flow_rate=None,
                      viscosity=None,
                      col1=xax,
                      col2=yax,
                      add_px_err=add_px_err,
                      px_um=px_um,
                      )
        try:
            isoel = isosource.get(**kwargs)
        except KeyError:
            warnings.warn("Could not find matching isoelastics for"+
                          " Setting: x={}, y={}, method: {}".
                          format(xax, yax, kwargs["method"]))
            isoel = None
    return isoel


def get_kde_kwargs(x, y, kde_type, xacc, yacc):
    """Copmutes optimal default KDE kwargs"""
    kde_kwargs = {}
    if kde_type == "multivariate":
        kde_kwargs["bw"] = [xacc, yacc]
    elif kde_type == "histogram":
        # The histogram accuracy is scaled by 1.8 to approximately
        # match the multivariate kde.
        try:
            binx = naninfminmaxdiff(x)/(1.8*xacc)
        except:
            binx = 5
        try:
            biny = naninfminmaxdiff(y)/(1.8*yacc)
        except:
            biny = 5
        binx = int(max(5, binx))
        biny = int(max(5, biny))
        kde_kwargs["bins"] = [binx, biny]
    return kde_kwargs
            
            
def my_log_auto_ticks(data_low, data_high,
                   bound_low, bound_high,
                   tick_interval, use_endpoints = True):
    """
    modified chaco.ticks.log_auto_ticks for displaying only
    the exponents of tens.
    """
    if data_low<=0.0:
        return []

    if data_low>data_high:
        data_low, data_high = data_high, data_low

    log_low = np.log10(data_low)
    log_high = np.log10(data_high)

    startlog = np.ceil(log_low)
    endlog = np.floor(log_high)
    interval = max(1, np.ceil((endlog-startlog)/9.0))
    expticks = np.arange(startlog, endlog, interval)
    expticks = np.concatenate([expticks, [endlog]])

    return 10**expticks


def naninfminmaxdiff(x):
    bad = np.isnan(x)+np.isinf(x)
    x = x[~bad]
    diff = (x.max()-x.min())
    return diff


# Load legacy isoelasticity lines (not part of dclab)
data_dir = resource_filename("shapeout", "data")
iso_file = os.path.join(data_dir, "isoel-analytical-area_um-deform_legacy.txt")
legacy_isoelastics = isoelastics.Isoelastics([iso_file])
