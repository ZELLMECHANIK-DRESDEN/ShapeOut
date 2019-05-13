#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - Analysis class"""
from __future__ import division, unicode_literals

import gc
import pathlib
import pkg_resources
import warnings
import sys

import chaco.api as ca
from chaco.color_mapper import ColorMapper
import numpy as np
import scipy.stats

import dclab
import dclab.definitions as dfn
from dclab.rtdc_dataset import config as dclab_config

from .settings import get_ignored_features, SettingsFile


if sys.version_info[0] == 2:
    str_classes = (str, unicode)
else:
    str_classes = str


class MultipleValuesError(BaseException):
    pass


class Analysis(object):
    """Stores several RT-DC data sets and useful methods

    This object contains
     - RT-DC data sets
     - common configuration parameters of the data sets
     - Plotting parameters
    """

    def __init__(self, data, config={}):
        """ Analysis data object.

        Parameters
        ----------
        data: str or list of (str, dclab.rtdc_dataset.RTDCBase)
            The data to load. The nature of `data` is inferred
            from its type:
            - list: A list of paths of measurement files or instances
                    of RTDCBase
        search_path: str
            In case `data` is a string, `search_path` is used to
            find missing files on disk.
        config: dict
            A configuration dictionary that will be applied to
            each RT-DC dataset before completing the configuration
            and data. The completion of the configuration takes
            place at the end of the initialization of this class and
            the configuration must be applied beforehand to make
            sure that parameters such as "emodulus" are computed.
        """
        # Start importing measurements
        self.measurements = []
        if isinstance(data, list):
            # New analysis
            for dd in data:
                if isinstance(dd, dclab.rtdc_dataset.RTDCBase):
                    rtdc_ds = dd
                elif (isinstance(dd, (str_classes, pathlib.Path)) and
                      pathlib.Path(dd).exists()):
                    rtdc_ds = dclab.new_dataset(dd)
                else:
                    raise ValueError("Data type not understood: {}".format(dd))
                self.measurements.append(rtdc_ds)
        else:
            raise ValueError("Argument not a list of files or " +
                             "measuremens: {}".format(data))

        # Set configuration (e.g. from previous analysis)
        if config:
            self.SetParameters(config)
        # Complete missing configuration parameters
        self._complete_config()

    def __getitem__(self, idx):
        return self.measurements[idx]

    def __iter__(self):
        for mm in self.measurements:
            yield mm

    def __len__(self):
        return len(self.measurements)

    def _clear(self):
        """Remove all attributes from this instance, making it unusable

        It is difficult to control how the chaco plots refer to a measurement
        object.

        """
        for _i in range(len(self.measurements)):
            mm = self.measurements.pop(0)
            # Deleting all the data in measurements!
            refs = gc.get_referrers(mm)
            for r in refs:
                if hasattr(r, "delplot"):
                    r.delplot()
                del r
            del mm
        # Reset contour accuracies
        self.reset_plot_accuracies()
        gc.collect()

    def _complete_config(self, measurements=None):
        """Complete configuration of all RT-DC datasets

        Sets configuration keywords that are not (necessarily)
        used/required by dclab.
        """
        if measurements is None:
            measurements = self.measurements

        for mm in measurements:
            # Update configuration with default values from Shape-Out,
            # but do not override anything.
            cfgold = mm.config.copy()
            mm.config.update(get_default_config())
            mm.config.update(cfgold)
            # Sensible values for default contour accuracies
            # Use Doane's formula
            defs = [["contour accuracy {}", self._doanes_formula_acc, 1/4],
                    ["kde accuracy {}", self._doanes_formula_acc, 1/2],
                    ]
            pltng = mm.config["plotting"]
            for kk, sc in zip(self.GetPlotAxes(), self.GetPlotScales()):
                for d, l, mult in defs:
                    var = d.format(kk)
                    if var not in pltng:
                        data = mm[kk]
                        if sc == "log":
                            data = np.log(data)
                        acc = l(data) * mult
                        # round to make it look pretty in the GUI
                        accr = float("{:.1e}".format(acc))
                        pltng[var] = accr
            # Check for missing min/max values and set them to zero
            for item in dfn.scalar_feature_names:
                appends = [" min", " max"]
                for a in appends:
                    if item + a not in mm.config["plotting"]:
                        mm.config["plotting"][item+a] = 0

    @staticmethod
    def _doanes_formula_acc(a):
        """Compute accuracy (bin width) based on Doane's formula"""
        # https://en.wikipedia.org/wiki/Histogram#Number_of_bins_and_width
        # https://stats.stackexchange.com/questions/55134/doanes-formula-for-histogram-binning
        bad = np.isnan(a) | np.isinf(a)
        data = a[~bad]
        n = data.size
        g1 = scipy.stats.skew(data)
        sigma_g1 = np.sqrt(6 * (n - 2) / ((n + 1) * (n + 3)))
        k = 1 + np.log2(n) + np.log2(1 + np.abs(g1) / sigma_g1)
        if len(data):
            acc = (data.max() - data.min()) / k
        else:
            acc = 1
        return acc

    def append(self, ds):
        self.measurements.append(ds)

    def ForceSameDataSize(self):
        """
        Force all measurements to have the same filtered size by setting
        the minimum possible value for ["Filtering"]["Limit Events"] and
        return that size.
        """
        # Reset limit filtering to get the correct number of events
        # This value will be overridden in the end.
        cfgreset = {"filtering": {"limit events": 0}}
        # This also calls apply_filter and comutes clean filters
        self.SetParameters(cfgreset)

        # Get minimum size
        minsize = np.inf
        for m in self.measurements:
            minsize = min(minsize, np.sum(m._filter))
        cfgnew = {"filtering": {"limit events": minsize}}
        self.SetParameters(cfgnew)
        return minsize

    def get_feat_range(self, feature, scale="linear", filtered=True,
                       update_config=True):
        """Return the current plotting range of a feature

        Parameters
        ----------
        feature: str
            Name of the feature for which the plotting range is computed
        scale: str
            Plotting scale, one of "log", "linear"
        filtered: bool
            If True, determine plotting range for filtered data
        update_config: bool
            If True and the current plotting range is invalid, update
            the current configuration. Invalid plotting ranges are
            length-zero intervals and, in the case of logarithmic scale,
            intervals with negative boundaries.

        Returns
        -------
        (rmin, rmax): tuple of floats
            Current/Correct plotting range
        """
        rmin = self.get_config_value("plotting", feature+" min")
        rmax = self.get_config_value("plotting", feature+" max")
        # update range if necessary
        # - "rmin == rmax" means the values *must* be determined automatically
        # - for log-scale, new ranges must be found to avoid plot errors
        if (rmin == rmax or
                (scale == "log" and (rmin <= 0 or rmax <= 0))):
            rmin, rmax = self.get_feat_range_opt(feature=feature,
                                                 scale=scale,
                                                 filtered=filtered)
            if update_config:
                # Set config keys
                newcfg = {"plotting": {feature + " min": rmin,
                                       feature + " max": rmax}}
                self.SetParameters(newcfg)
        return rmin, rmax

    def get_feat_range_opt(self, feature, scale="linear", filtered=True):
        """Return the optimal plotting range of a feature for all measurements

        Parameters
        ----------
        feature: str
            Name of the feature for which the plotting range is computed
        scale: str
            Plotting scale, one of "log", "linear"
        filtered: bool
            If True, determine plotting range for filtered data

        Returns
        -------
        (rmin, rmax): tuple of floats
            Optimal plotting range

        Notes
        -----
        For `feature="deform"`, the returned plotting range is always (0, 0.2).
        If the scale of the current configuration is set to "log", then a
        heuristic method is used to determine the plot range: Fluorescence
        maxima data (e.g. "fl1_max" or "fl2_max_ctc") will get an rmin value
        of 1. The value of rmin is determined using a combination
        of mean and std. If indeterminable, values or are set to .1 (rmin)
        or 1 (rmax).
        """
        if scale not in ["linear", "log"]:
            raise ValueError("`scale` must be one of 'linear', 'log'.")
        if feature == "deform":
            if scale == "log":
                rmin = .01
            else:
                rmin = 0
            rmax = 0.2
        else:
            # find min/max values of all measurements
            rmin = np.inf
            rmax = -np.inf
            for mm in self.measurements:
                mmf = mm[feature]
                if filtered:
                    mmf = mmf[mm.filter.all]
                if mmf.size:  # prevent searching for min/max in empty array
                    rmin = min(rmin, np.nanmin(mmf))
                    rmax = max(rmax, np.nanmax(mmf))
                # check for logarithmic plots
                if scale == "log":
                    if rmin <= 0:
                        if feature.startswith("fl") and feature.count("_max"):
                            # fluorescence maxima data
                            rmin = 1
                        else:
                            # compute std and mean (nans are always False)
                            ld = np.log(mmf[mmf > 0])
                            if len(ld):
                                rmin = np.exp(ld.mean() - 2 * ld.std())
                            else:
                                # generic default
                                rmin = .1
                    if rmax <= 0:
                        # generic default
                        rmax = 1
        # fail-safe
        if np.isinf(rmin) and np.isinf(rmax):
            rmin = rmax = 1
        elif np.isinf(rmin):
            rmin = rmax - 1
        elif np.isinf(rmax):
            rmax = rmin + 1
        return rmin, rmax

    def get_config_value(self, section, key):
        """Return the section/key value of all measurements

        Parameters
        ----------
        section: str
            Configuration section, e.g. "imaging", "filtering", or "plotting"
        key: str
            Configuration key within `section`

        Returns
        -------
        value: multiple types
            The configuration key value

        Raises
        ------
        MultipleValuesError: if not all measurements share the same value

        Notes
        -----
        Using this function to retrieve section/key values ensures that the
        value is identical for all measurements.
        """
        values = []
        for mm in self.measurements:
            values.append(mm.config[section][key])
        all_same = np.all(np.array(values) == values[0])
        if not all_same:
            msg = "Multiple values encountered for [{}]: {}".format(section,
                                                                    key)
            raise MultipleValuesError(msg)
        return mm.config[section][key]

    def GetCommonParameters(self, key):
        """
        For as key (e.g. "Filtering") find all parameters that are given
        for every measurement in the analysis.
        """
        retdict = dict()
        if key in self.measurements[0].config:
            s = set(self.measurements[0].config[key].items())
            for m in self.measurements[1:]:
                s2 = set(m.config[key].items())
                s = s & s2
            for item in s:
                retdict[item[0]] = item[1]
        return retdict

    def GetContourColors(self):
        colors = []
        for mm in self.measurements:
            colors.append(mm.config["Plotting"]["Contour Color"])
        return colors

    def GetNames(self):
        """ Returns the titles of all measurements """
        warnings.warn("Please use GetTitles", DeprecationWarning)
        return self.GetTitles()

    def GetPlotAxes(self, mid=0):
        p = self.GetParameters("plotting", mid)
        return [p["axis x"].lower(), p["axis y"].lower()]

    def GetPlotGeometry(self, mid=0):
        p = self.GetParameters("Plotting", mid)
        return (int(p["Rows"]), int(p["Columns"]),
                int(p["Contour Plot"]), int(p["Legend Plot"]))

    def GetPlotScales(self, mid=0):
        p = self.GetParameters("Plotting", mid)
        return [p["scale x"].lower(), p["scale y"].lower()]

    def GetStatisticsBasic(self):
        """
        Computes Mean, Avg, etc for all data sets and returns two lists:
        The headings and the values.
        """
        datalist = []
        head = None
        for mm in self.measurements:
            features = [mm.config["plotting"]["axis x"].lower(),
                        mm.config["plotting"]["axis y"].lower()]
            h, v = dclab.statistics.get_statistics(mm, features=features)
            # Make sure all features are equal
            if head is not None:
                assert head == h, "'{}' has wrong features!".format(mm.title)
            else:
                head = h
            datalist.append([mm.title]+v)

        head = ["Data set"] + head
        return head, datalist

    def GetFilenames(self):
        """Returns paths of measurements"""
        names = list()
        for mm in self.measurements:
            names.append(mm.path)
        return names

    def GetTitles(self):
        """ Returns the titles of all measurements """
        return [ds.title for ds in self]

    def GetUncommonParameters(self, key):
        # Get common parameters first:
        com = self.GetCommonParameters(key)
        retdict = dict()
        if key in self.measurements[0].config:
            s = set(self.measurements[0].config[key].items())
            uncom = set(com.items()) ^ s
            for nn in self.measurements[1:]:
                s2 = set(nn.config[key].items())
                uncom2 = set(com.items()) ^ s2

                newuncom = dict()
                uncom.symmetric_difference_update(uncom2)
                for _i in range(len(uncom)):
                    item = uncom.pop()
                    newuncom[item[0]] = None
                uncom = set(newuncom.items())

            for item in uncom:
                vals = list()
                for mm in self.measurements:
                    if item[0] in mm.config[key]:
                        vals.append(mm.config[key][item[0]])
                    else:
                        vals.append(None)
                        msg = "Missing key {}: {} in {}!".format(key,
                                                                 item[0],
                                                                 mm)
                        warnings.warn(msg)
                retdict[item[0]] = vals
        return retdict

    def GetUnusableAxes(self):
        """
        Unusable axes are axes that are not shared by all measurements
        or that are ignored by default.

        See Also
        --------
        GetUsableAxes
        """
        unusable = []
        for ax in dfn.scalar_feature_names:
            if ax in get_ignored_features():
                unusable.append(ax)
                continue
            for mm in self.measurements:
                # Get the attribute name for the axis
                if ax not in mm:
                    unusable.append(ax)
                    break
        return unusable

    def GetUsableAxes(self):
        """
        Usable axes are axes that are shared by all measurements
        A measurement does not have an axis, if all values along
        that axis are zero.

        See Also
        --------
        GetUnusableAxes
        """
        unusable = self.GetUnusableAxes()
        usable = []
        for ax in dfn.scalar_feature_names:
            if ax not in unusable:
                usable.append(ax)
        return usable

    def GetParameters(self, key, mid=0, filter_for_humans=True):
        """Get parameters that all measurements share."""
        conf = self.measurements[mid].config.copy()[key]
        unusable_axes = self.GetUnusableAxes()
        pops = []
        for k in conf:
            # remove axes that are not owned by all measurements
            if k.endswith(" max"):
                ax = k[:-4]
                if ax in unusable_axes:
                    pops.append("kde accuracy {}".format(ax))
                    pops.append("contour accuracy {}".format(ax))
                    pops.append("{} min".format(ax))
                    pops.append("{} max".format(ax))
        for k in list(set(pops)):
            if k in conf:
                conf.pop(k)

        return conf

    def reset_plot(self):
        self.reset_plot_accuracies()
        self.reset_plot_ranges()

    def reset_plot_accuracies(self, feature_names=None):
        """ Set initial (heuristic) accuracies for all plots.

        It is not always easy to determine the correct accuracy for
        the contour plots. This method sets these accuracies for the user.

        All keys of the active axes are changed, e.g.:
          - "contour accuracy area"
          - "contour accuracy defo"
          - "kde accuracy defo"
          - "kde accuracy defo"

        Note that the accuracies are not updated when the key
        ["Plotting"]["Contour Fix Scale"] is set to `True` for the
        first measurement of the analysis.
        """
        # check if updating is disabled:
        if (len(self.measurements) == 0 or
                self.measurements[0].config["plotting"]["contour fix scale"]):
            return

        if feature_names is None:
            feature_names = dfn.scalar_feature_names

        # Remove contour accuracies for the current plots
        for key in feature_names:
            for mm in self.measurements:
                for var in ["contour accuracy {}".format(key),
                            "kde accuracy {}".format(key)]:
                    if var in mm.config["plotting"]:
                        mm.config["plotting"].pop(var)
        # Set default accuracies
        self._complete_config()

    def reset_plot_ranges(self):
        """Reset plotting range"""
        for key in dfn.scalar_feature_names:
            for mm in self.measurements:
                if not mm.config["plotting"]["fix range"]:
                    for var in ["{} min".format(key),
                                "{} max".format(key)]:
                        if var in mm.config["plotting"]:
                            mm.config["plotting"].pop(var)
        # Set defaul values
        self._complete_config()

    def PolygonFilterRemove(self, filt):
        """
        Removes a polygon filter from all elements of the analysis.
        """
        for mm in self.measurements:
            try:
                mm.polygon_filter_rm(filt)
            except ValueError:
                pass

    def set_config_value(self, section, key, value):
        """Set the section/key value for all measurements

        Parameters
        ----------
        section: str
            Configuration section, e.g. "imaging", "filtering", or "plotting"
        key: str
            Configuration key within `section`
        value:
            Value to set
        """
        for mm in self.measurements:
            mm.config[section][key] = value

    def SetContourColors(self, colors=None):
        """ Sets the contour colors.

        If colors is given and if the number of colors is equal or
        greater than the number of measurements, then the colors are
        applied to the measurement. Otherwise, default colors are used.
        """
        if len(self.measurements) > 1:
            if colors is None or len(colors) < len(self.measurements):
                # set colors
                colormap = darkjet(ca.DataRange1D(low=0, high=1),
                                   steps=len(self.measurements))
                colors = colormap.color_bands
                newcolors = list()
                for color in colors:
                    color = [float(c) for c in color]
                    newcolors.append(color)
                colors = newcolors

            for ii, mm in enumerate(self.measurements):
                mm.config["plotting"]["contour color"] = colors[ii]

    def SetParameters(self, newcfg):
        """Update the RT-DC dataset configuration"""
        upcfg = {}
        if "filtering" in newcfg:
            upcfg["filtering"] = newcfg["filtering"].copy()
        if "plotting" in newcfg:
            upcfg["plotting"] = newcfg["plotting"].copy()
            pl = upcfg["plotting"]

            # prevent applying individual things to all measurements
            ignorelist = ["contour color"]
            pops = []
            for skey in pl:
                if skey in ignorelist:
                    pops.append(skey)
            for skey in pops:
                pl.pop(skey)

            if "plotting" in self[0].config:
                scalex, scaley = self.GetPlotScales()
                xax, yax = self.GetPlotAxes()
                # If the scale changed, recompute kde and contour accuracies.
                if "scale x" in pl and pl["scale x"] != scalex:
                    self.set_config_value("plotting", "scale x", pl["scale x"])
                    self.reset_plot_accuracies(feature_names=[xax])
                    pl.pop("kde accuracy {}".format(xax))
                    pl.pop("contour accuracy {}".format(xax))
                if "scale y" in pl and pl["scale y"] != scaley:
                    self.set_config_value("plotting", "scale y", pl["scale y"])
                    self.reset_plot_accuracies(feature_names=[yax])
                    pl.pop("kde accuracy {}".format(yax))
                    pl.pop("contour accuracy {}".format(yax))
            # check for inverted plotting ranges
            for feat in dfn.scalar_feature_names:
                fmin = feat + " min"
                fmax = feat + " max"
                if (fmin in pl and
                    fmax in pl and
                        pl[fmin] > pl[fmax]):
                    msg = "inverting plot range: {} > {}".format(fmin, fmax)
                    warnings.warn(msg)
                    pl[fmin], pl[fmax] = pl[fmax], pl[fmin]
            # make sure that x- and y-axes are present in all measurements
            if "axis x" in pl:
                for mm in self.measurements:
                    if pl["axis x"] not in mm:
                        pl["axis x"] = "area_um"
                        break
            if "axis y" in pl:
                for mm in self.measurements:
                    if pl["axis y"] not in mm:
                        pl["axis y"] = "deform"
                        break
        if "analysis" in newcfg:
            upcfg["analysis"] = newcfg["analysis"].copy()
            ignorelist = ["regression treatment", "regression repetition"]
            pops = []
            for skey in upcfg["analysis"]:
                if skey in ignorelist:
                    pops.append(skey)
            for skey in pops:
                upcfg["analysis"].pop(skey)
        if "calculation" in newcfg:
            upcfg["calculation"] = newcfg["calculation"].copy()

        for mm in self.measurements:
            # update configuration
            mm.config.update(upcfg)
        for mm in self.measurements:
            # apply filter in separate loop (safer for hierarchies)
            mm.apply_filter()

        # Trigger computation of kde/contour accuracies for ancillary features
        self._complete_config()


def darkjet(myrange, **traits):
    """Generator function for the 'darkjet' colormap. """
    _data = {'red': ((0., 0, 0), (0.35, 0.0, 0.0), (0.66, .3, .3), (0.89, .4, .4),
                     (1, 0.5, 0.5)),
             'green': ((0., 0.0, 0.0), (0.125, .1, .10), (0.375, .4, .4), (0.64, .3, .3),
                       (0.91, 0.2, 0.2), (1, 0, 0)),
             'blue': ((0., 0.7, 0.7), (0.11, .5, .5), (0.34, .4, .4), (0.65, 0, 0),
                      (1, 0, 0))}
    return ColorMapper.from_segment_map(_data, range=myrange, **traits)


# TODO: (Python3)
# - decorate this method with a cache
def get_default_config():
    cfg_dir = pkg_resources.resource_filename("shapeout", "cfg")
    cfg_file = pathlib.Path(cfg_dir) / "default.cfg"
    cfg = dclab_config.load_from_file(cfg_file)
    return cfg


def remove_nan_inf(x):
    for issome in [np.isnan, np.isinf]:
        xsome = issome(x)
        x = x[~xsome]
    return x
