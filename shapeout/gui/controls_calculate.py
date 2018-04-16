#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import wx

from ..settings import SettingsFile

from . import confparms
from .controls_subpanel import SubPanel

class SubPanelCalculate(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = SettingsFile()
        self.key = "Calculate"


    def make_crosstalk_choices(self, analysis):
        gen = wx.StaticBox(self, label="Fluorescence maximum crosstalk compensation")
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        crosstalk = {}
        for i in [1, 2, 3]:
            for j in [1, 2, 3]:
                if i == j:
                    continue
                crosstalk["crosstalk fl{}{}".format(i, j)] = 0
        
        if analysis is not None:
            # get common parameters
            sizer_bag = wx.GridBagSizer(hgap=20, vgap=5)
            mm = analysis.measurements[0]

            if "calculation" in mm.config:
                # override default variables
                calc = mm.config["calculation"]
                for key in crosstalk:
                    if key in calc:
                        crosstalk[key] = calc[key]

            # Model to apply
            sizer_bag.Add(wx.StaticText(self, label="Spill from channel i to channel j"),
                          (0,0), span=(1,4))
            self.WXcrosstalk_sp = []
            pos = 4
            for i in [1, 2, 3]:
                for j in [1, 2, 3]:            
                    if i == j:
                        continue
                    line = pos // 4
                    col = pos % 4
                    label = "{} to {}:".format(i, j)
                    name = "crosstalk fl{}{}".format(i, j)
                    value = str(crosstalk[name])
                    sizer_bag.Add(wx.StaticText(self, label=label), (line, col))
                    spctl = wx.SpinCtrlDouble(self, value=value, min=0, max=10, inc=.1, name=name)
                    spctl.SetDigits(3)
                    sizer_bag.Add(spctl, (line, col+1))
                    pos += 2
                    self.WXcrosstalk_sp.append(spctl)

            compute_btn = wx.Button(self, label="Crosstalk compensation")
            sizer_bag.Add(compute_btn, (4,0), span=(1,4), flag=wx.EXPAND|wx.ALL)
            self.Bind(wx.EVT_BUTTON, self.OnCrosstalkCorrection, compute_btn)
            
            hbox.Add(sizer_bag)
            
        return hbox
        

    
    def make_emodulus_choices(self, analysis):
        gen = wx.StaticBox(self, label="Elastic modulus")
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        # default variables
        medium = "CellCarrier"
        model = "elastic sphere"
        temperature = 23.0
        viscosity = 0.0

        if analysis is not None:
            # get common parameters
            sizer_bag = wx.GridBagSizer(hgap=20, vgap=5)
            mm = analysis.measurements[0]

            if "calculation" in mm.config:
                # override default variables
                calc = mm.config["calculation"]
                if "emodulus model" in calc:
                    model = calc["emodulus model"]
                if "emodulus medium" in calc:
                    medium = calc["emodulus medium"]
                if "emodulus temperature" in calc:
                    temperature =calc["emodulus temperature"]
                if "emodulus viscosity" in calc:
                    viscosity = calc["emodulus viscosity"]

            # Model to apply
            sizer_bag.Add(wx.StaticText(self, label="Model:"), (0,0))
            choices = confparms.get_config_entry_choices("calculation",
                                                         "emodulus model")
            self.WXCB_model = wx.ComboBox(self, -1, choices=choices,
                                    value=model, name="emodulus model",
                                    style=wx.CB_DROPDOWN|wx.CB_READONLY)
            sizer_bag.Add(self.WXCB_model, (0,1), flag=wx.EXPAND|wx.ALL)
            
            # Medium to use
            sizer_bag.Add(wx.StaticText(self, label="Medium:"), (1,0))
            self.axes = analysis.GetUsableAxes()
            mediumlist = confparms.get_config_entry_choices("calculation",
                                                            "emodulus medium")
            self.WXCB_medium = wx.ComboBox(self, -1, choices=mediumlist,
                                         value=medium, name="emodulus medium",
                                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
            sizer_bag.Add(self.WXCB_medium, (1,1), flag=wx.EXPAND|wx.ALL)
            
            # Viscosity to use
            sizer_bag.Add(wx.StaticText(self, label="Viscosity [mPa·s]:"), (2,0))
            self.WXSC_visc = wx.SpinCtrlDouble(self, -1, name="viscosity",
                                               min=0.5, max=10000, inc=0.0001)
            self.WXSC_visc.SetValue(viscosity)
            sizer_bag.Add(self.WXSC_visc, (2,1), flag=wx.EXPAND|wx.ALL)

            # Temperature to use
            sizer_bag.Add(wx.StaticText(self, label="Temperature [°C]:"), (3,0))
            self.WXSC_temp = wx.SpinCtrlDouble(self, -1, name="temperature",
                                               min=0.0, max=100, inc=0.01)
            self.WXSC_temp.SetValue(temperature)
            sizer_bag.Add(self.WXSC_temp, (3,1), flag=wx.EXPAND|wx.ALL)
            
            compute_btn = wx.Button(self, label="Compute elastic modulus")
            sizer_bag.Add(compute_btn, (4,0), span=(1,2), flag=wx.EXPAND|wx.ALL)
            self.Bind(wx.EVT_BUTTON, self.OnComputeEmodulus, compute_btn)
            
            self.BindEnableName(ctrl_source="emodulus medium",
                                value="Other",
                                ctrl_targets=["viscosity"])
            
            mediumlist.remove("Other")
            self.BindEnableName(ctrl_source="emodulus medium",
                                value=mediumlist,
                                ctrl_targets=["temperature"])
            
            hbox.Add(sizer_bag)
            
        return hbox


    def OnCrosstalkCorrection(self, e=None):
        """Set crosstalk values for all measurements
        """
        ctdict = {}
        for sp in self.WXcrosstalk_sp:
            ctdict[sp.GetName()] = sp.GetValue()
        self.analysis.SetParameters({"calculation": ctdict})
        # Update filtering
        self.funcparent.OnChangeFilter()


    def OnComputeEmodulus(self, e=None):
        """
        Compute Emodulus for all measurements
        """
        model = self.WXCB_model.GetValue()
        medium = self.WXCB_medium.GetValue()
        viscosity = self.WXSC_visc.GetValue()
        temperature = self.WXSC_temp.GetValue()

        self.analysis.SetParameters({"calculation":
                                     {"emodulus model":model,
                                      "emodulus medium":medium,
                                      "emodulus viscosity":viscosity,
                                      "emodulus temperature":temperature}
                                     })
        # Update filtering
        self.funcparent.OnChangeFilter()


    def UpdatePanel(self, analysis=None):
        if analysis is None:
            analysis = self.analysis
        self.analysis = analysis

        self.ClearSubPanel()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        emodbox = self.make_emodulus_choices(analysis)
        sizer.Add(emodbox)

        crossbox = self.make_crosstalk_choices(analysis)
        sizer.Add(crossbox)
                
        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerv)
        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
