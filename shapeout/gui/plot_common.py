#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Common plotting methods"""
from __future__ import print_function, division, unicode_literals

import chaco
import numpy as np
import scipy.stats

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


def get_kde_kwargs(x, y, kde_type, xacc, yacc):
    """Copmutes optimal default KDE kwargs"""
    kde_kwargs = {}
    if kde_type == "multivariate":
        kde_kwargs["bw"] = [xacc, yacc]
    elif kde_type == "histogram":
        #Use Doanes formula to determine the number of bins
        g1_x = scipy.stats.skew(x)
        g1_y = scipy.stats.skew(y)
        
        bad = np.isnan(x)+np.isinf(x)
        l = len(x[~bad]) #Number values that are not nan or inf
        sigma_g1 = np.sqrt((6.0*(l-2.0))/((l+1.0)*(l+3.0)))
        #Use the values xacc and yacc to allow the user to adjust the binsize
        binx = xacc*int(1.0+np.log2(l)+np.log2(1+abs(g1_x)/sigma_g1))
        biny = yacc*int(1.0+np.log2(l)+np.log2(1+abs(g1_y)/sigma_g1))
        
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
    interval = np.ceil((endlog-startlog)/9.0)
    expticks = np.arange(startlog, endlog, interval)
    expticks = np.concatenate([expticks, [endlog]])

    return 10**expticks


def naninfminmaxdiff(x):
    bad = np.isnan(x)+np.isinf(x)
    x = x[~bad]
    diff = (x.max()-x.min())
    return diff
