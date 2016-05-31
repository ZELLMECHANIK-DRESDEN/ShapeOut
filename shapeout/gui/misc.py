#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - miscellaneous methods for GUI

"""
from __future__ import division, print_function

import chaco
import numpy as np
import wx
from . import icon


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


def getMainIcon(pxlength=32):
    """ *pxlength* is the side length in pixels of the icon """
    # Set window icon
    iconBMP = icon.getMainBitmap()
    # scale
    image = wx.ImageFromBitmap(iconBMP)
    image = image.Scale(pxlength, pxlength, wx.IMAGE_QUALITY_HIGH)
    iconBMP = wx.BitmapFromImage(image)
    iconICO = wx.IconFromBitmap(iconBMP)
    return iconICO
            
            
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
