#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import copy
import dclab
import wx
from wx.lib.scrolledpanel import ScrolledPanel
import warnings

from dclab import definitions as dfn

from .. import tlabwrap

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
        gen = wx.StaticBox(self, label=_(key))
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:
            items = analysis.GetCommonParameters(key).items()
            items2 = analysis.GetUncommonParameters(key).items()

            # Ignore keys
            items = [it for it in items if not it[0].lower() in ignore]
            items2 = [it for it in items2 if not it[0].lower() in ignore]

            multiplestr = _("(multiple)")
            for item in items2:
                items.append((item[0], multiplestr))
            items.sort()
            sgen = wx.FlexGridSizer(len(items), 2)
            
            for item in items:
                a = wx.StaticText(self, label=item[0])
                b = wx.StaticText(self, label=str(item[1]))
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
        ignore_axes = tlabwrap.IGNORE_AXES+analysis.GetUnusableAxes()
        choices = get_config_entry_choices(key, item[0],
                                           ignore_axes=ignore_axes)
        if len(choices) != 0:
            if choices[0] in dclab.dfn.axlabels:
                human_choices = [ _(dclab.dfn.axlabels[c]) for c in choices]
            else:
                human_choices = choices

            a = wx.StaticText(self, label=_(item[0]))
            # sort choices with _()?
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

        elif (get_config_entry_dtype(key, item[0]) == bool or
              str(item[1]).capitalize() in ["True", "False"]):
            a = wx.CheckBox(self, label=_(item[0]), name=item[0])
            a.SetValue(item[1])
            stemp.Add(a)
        else:
            a = wx.StaticText(self, label=_(item[0]))
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
                    tar.Enable(source.IsChecked() in value)
                    if evt is not None:
                        evt.Skip()
                event = wx.EVT_CHECKBOX
            elif isinstance(source, wx._controls.ComboBox):
                def method(evt=None, tar=tar, value=value):
                    tar.Enable(source.GetValue() in value)
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
            default = tlabwrap.GetDefaultConfiguration(self.key)
            for c in ctrls:
                subkey = c.GetName()
                if subkey in default:
                    subkeys.append(subkey)
            self.funcparent.Reset(self.key, subkeys)


    def UpdatePanel(self, *args, **kwargs):
        """ Overwritten by subclass """
        pass


def get_config_entry_choices(key, subkey, ignore_axes=[]):
    """ Returns the choices for a parameter, if any
    """
    key = key.lower()
    subkey = subkey.lower()
    ignore_axes = [a.lower() for a in ignore_axes]
    ## Manually defined types:
    choices = []
    
    if key == "plotting":
        if subkey == "kde":
            choices = list(dclab.kde_methods.methods.keys())

        elif subkey in ["axis x", "axis y"]:
            choices = copy.copy(dfn.uid)
            # remove unwanted axes
            for choice in ignore_axes:
                if choice in choices:
                    choices.remove(choice)
   
        elif subkey in ["rows", "columns"]:
            choices = [ str(i) for i in range(1,6) ]
        elif subkey in ["scatter marker size"]:
            choices = [ str(i) for i in range(1,5) ]
        elif subkey.count("scale "):
            choices = ["linear", "log"]
    return choices


def get_config_entry_dtype(key, subkey, cfg=None):
    """ Returns dtype of the parameter as defined in dclab.cfg
    """
    key = key.lower()
    subkey = subkey.lower()
    #default
    dtype = str

    ## Define dtypes and choices of cfg content
    # Iterate through cfg to determine standard dtypes
    cfg_init = tlabwrap.cfg.copy()  
    if cfg is None:
        cfg = cfg_init.copy()
   
    if key in cfg_init and subkey in cfg_init[key]:
        dtype = cfg_init[key][subkey].__class__
    else:
        try:
            dtype = cfg[key][subkey].__class__
        except KeyError:
            dtype = float

    return dtype