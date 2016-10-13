#!/usr/bin/python
# -*- coding: utf-8 -*-
import dclab
import wx
from wx.lib.scrolledpanel import ScrolledPanel

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


    def _box_from_cfg_read(self, analysis, key):
        gen = wx.StaticBox(self, label=_(key))
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:
            items = analysis.GetCommonParameters(key).items()
            items2 = analysis.GetUncommonParameters(key).items()

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
        choices = dclab.config.get_config_entry_choices(key, item[0],
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
                idc = choices.index(item[1])
                c.SetSelection(idc)
            stemp.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
            stemp.Add(c)

        elif (dclab.config.get_config_entry_dtype(key, item[0]) == bool or
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
            print(subkeys)
            self.funcparent.Reset(self.key, subkeys)
            

    def UpdatePanel(self, *args, **kwargs):
        """ Overwritten by subclass """
        pass