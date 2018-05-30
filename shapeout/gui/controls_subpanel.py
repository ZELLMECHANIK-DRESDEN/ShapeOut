#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import warnings

import dclab
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from . import confparms


class SubPanel(ScrolledPanel):
    def __init__(self, parent, funcparent=None, *args, **kwargs):
        """
        Notebook page dummy with methods
        """
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        self.SetupScrolling(scroll_y=True)
        self.SetupScrolling(scroll_x=True)
        self.analysis = None
        self.key = None
        self.funcparent = funcparent


    def _box_from_cfg_read(self, analysis, key, ignore=[]):
        """Generate user interface from configuration keys
        
        analysis: shapeout analysis instance
            The data
        key: str
            The dictionary key from which to obtain the
            user interface values
        ignore: list of str
            Lower case list of subkeys to not include in the
            interface
        """
        gen = wx.StaticBox(self, label=key)
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:
            items = analysis.GetCommonParameters(key).items()
            items2 = analysis.GetUncommonParameters(key).items()

            # Ignore keys
            items = [it for it in items if not it[0].lower() in ignore]
            items2 = [it for it in items2 if not it[0].lower() in ignore]

            multiplestr = "(multiple)"
            for item in items2:
                items.append((item[0], multiplestr))
            items.sort()
            sgen = wx.FlexGridSizer(len(items), 2)
            
            for item in items:
                a = wx.StaticText(self, label=item[0])
                # This is a hacky temporary workaround as long as we are
                # in WxPython to display nice string representations:
                if item[1] == multiplestr:
                    label = multiplestr
                elif item[0] == "pixel size":
                    label = "{:.3f}".format(item[1])
                elif item[0] in ["flow rate", "flow rate sample", "flow rate sheath"]:
                    label = "{:.5f}".format(item[1])
                else:
                    label = str(item[1])
                b = wx.StaticText(self, label=label)
                if item[1] == multiplestr:
                    a.Disable()
                    b.Disable()
                sgen.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
                sgen.Add(b, 0, wx.ALIGN_CENTER_VERTICAL)
            sgen.Layout()
            hbox.Add(sgen)
        return hbox


    def _create_type_wx_controls(self, analysis, key, item):
        """ Create a wx control whose type is inferred by item
        
        Returns a sizer
        """
        stemp = wx.BoxSizer(wx.HORIZONTAL)
        # these axes should not be displayed in the UI
        ignore_axes = analysis.GetUnusableAxes()
        choices = confparms.get_config_entry_choices(key, item[0],
                                           ignore_axes=ignore_axes)
        if choices:
            if choices[0] in dclab.dfn.scalar_feature_names:
                human_choices = [ dclab.dfn.feature_name2label[c] for c in choices]
            elif key.lower() == "plotting" and item[0] == "isoelastics":
                # add the <0.8.4 version info to prevent user confusion
                human_choices = copy.copy(choices)
                idl = choices.index("legacy")
                human_choices[idl] = "legacy (prior to version 0.8.4)"
            else:
                human_choices = choices

            a = wx.StaticText(self, label=item[0])
            c = wx.ComboBox(self, -1, choices=human_choices,
                            value=unicode(item[1]), name=item[0],
                            style=wx.CB_DROPDOWN|wx.CB_READONLY)
            c.data = choices
            if not isinstance(item[1], (str, unicode)):
                # this is important for floats and ints
                for ch in choices:
                    if float(ch) == float(item[1]):
                        c.SetValue(ch)
            else:
                # this does not work for floats and ints
                idc = choices.index(item[1].lower())
                c.SetSelection(idc)
            stemp.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
            stemp.Add(c)

        elif (confparms.get_config_entry_dtype(key, item[0]) == bool or
              str(item[1]).capitalize() in ["True", "False"]):
            a = wx.CheckBox(self, label=item[0], name=item[0])
            a.SetValue(item[1])
            stemp.Add(a)
        else:
            a = wx.StaticText(self, label=item[0])
            b = wx.TextCtrl(self, value=str(item[1]), name=item[0])
            stemp.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
            stemp.Add(b)
        return stemp


    def BindEnableName(self, ctrl_source, value, ctrl_targets):
        """Convenience function to auto-enable or -disable controls
        
        Parameters
        ----------
        ctrl_source: name of a wx control
            The source control
        value: bool or str or list of str
            The value of the source control
        ctrl_targets: list of names of wx controls
            The controls to enable or disable depending on `value`
        """
        if not isinstance(value, list):
            value=[value]
        ctrl_source = ctrl_source.lower()
        ctrl_targets = [t.lower() for t in ctrl_targets]
        # Find source
        for c in self.GetChildren():
            if c.GetName()==ctrl_source:
                source=c
                break
        else:
            raise ValueError("Could not find source '{}'".format(ctrl_source))

        # Find targets
        targets = []
        for c in self.GetChildren():
            if c.GetName() in ctrl_targets:
                targets.append(c)

        assert len(targets) == len(ctrl_targets), "Could not find all targets!"

       
        for tar in targets:
            if isinstance(source, wx._controls.CheckBox):
                def method(evt=None, tar=tar, value=value):
                    try:
                        tar.Enable(source.IsChecked() in value)
                    except wx.PyDeadObjectError:
                        pass
                    if evt is not None:
                        evt.Skip()
                event = wx.EVT_CHECKBOX
            elif isinstance(source, wx._controls.ComboBox):
                def method(evt=None, tar=tar, value=value):
                    try:
                        tar.Enable(source.GetValue() in value)
                    except wx.PyDeadObjectError:
                        pass                    
                    if evt is not None:
                        evt.Skip()
                event = wx.EVT_COMBOBOX
            elif source.GetLabel() == "":
                warnings.warn("Empty label!")
                continue
            self.Bind(event, method, source)
            # Call the method to set the defaults
            method()


    def ClearSubPanel(self):
        for item in self.GetChildren():
            item.Hide()
            self.RemoveChild(item)
            item.Destroy()


    def OnReset(self, e=None):
        """ Reset all parameters that are defined in this panel.
        
        It is important, that the Name for each wxWidget is set to
        something available in the default configuration and that
        self.key is set to a valid key, e.g. "Plotting" or "Filtering".
        """
        if self.key is not None:
            # Get the controls that we change
            ctrls = self.GetChildren()
            subkeys = list()
            # identify controls via their name correspondence in the cfg
            default = confparms.GetDefaultConfiguration(self.key)
            for c in ctrls:
                subkey = c.GetName()
                if subkey in default:
                    subkeys.append(subkey)
            self.funcparent.Reset(self.key, subkeys)


    def UpdatePanel(self, *args, **kwargs):
        """ Overwritten by subclass """
        pass


    def UpdateScrolling(self):
        self.SetupScrolling(scroll_y=True)
        self.SetupScrolling(scroll_x=True)
