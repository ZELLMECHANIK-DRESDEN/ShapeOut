#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import dclab
import wx

from ..configuration import ConfigurationFile
from .. import tlabwrap

from .controls_subpanel import SubPanel

class SubPanelCalculate(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = ConfigurationFile()
        self.key = "Calculate"

    
    def make_emodulus_choices(self, analysis):
        gen = wx.StaticBox(self, label=_("Elastic modulus"))
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:
            # get common parameters
            sizer_bag = wx.GridBagSizer(hgap=20, vgap=5)

            # Model to apply
            sizer_bag.Add(wx.StaticText(self, label=_("Model:")), (0,0))
            choices = tlabwrap.get_config_entry_choices("calculation",
                                                        "emodulus model")
            model=analysis.measurements[0].config["calculation"]["emodulus model"]
            self.WXCB_model = wx.ComboBox(self, -1, choices=choices,
                                    value=model, name="emodulus model",
                                    style=wx.CB_DROPDOWN|wx.CB_READONLY)
            sizer_bag.Add(self.WXCB_model, (0,1), flag=wx.EXPAND|wx.ALL)
            
            # Medium to use
            sizer_bag.Add(wx.StaticText(self, label=_("Medium:")), (1,0))
            self.axes = analysis.GetUsableAxes()
            mediumlist = tlabwrap.get_config_entry_choices("calculation",
                                                           "emodulus medium")
            medium=analysis.measurements[0].config["calculation"]["emodulus medium"]
            self.WXCB_medium = wx.ComboBox(self, -1, choices=mediumlist,
                                         value=medium, name="emodulus medium",
                                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
            sizer_bag.Add(self.WXCB_medium, (1,1), flag=wx.EXPAND|wx.ALL)
            
            # Viscosity to use
            sizer_bag.Add(wx.StaticText(self, label=_("Viscosity [mPa·s]:")), (2,0))
            self.WXSC_visc = wx.SpinCtrlDouble(self, -1, name="viscosity",
                                               min=0.5, max=10000, inc=0.0001)
            self.WXSC_visc.SetValue(0.0)
            sizer_bag.Add(self.WXSC_visc, (2,1), flag=wx.EXPAND|wx.ALL)

            # Temperature to use
            sizer_bag.Add(wx.StaticText(self, label=_("Temperature [°C]:")), (3,0))
            self.WXSC_temp = wx.SpinCtrlDouble(self, -1, name="temperature",
                                               min=0.0, max=100, inc=0.01)
            self.WXSC_temp.SetValue(23.0)
            sizer_bag.Add(self.WXSC_temp, (3,1), flag=wx.EXPAND|wx.ALL)
            
            compute_btn = wx.Button(self, label=_("Compute elastic modulus"))
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


    def OnComputeEmodulus(self, e=None):
        """
        Compute Emodulus for all measurements
        """
        model = self.WXCB_model.GetValue()
        medium = self.WXCB_medium.GetValue()
        viscosity = self.WXSC_visc.GetValue()
        temperature = self.WXSC_temp.GetValue()

        self.analysis.SetParameters({"calculation":{"emodulus model":model},
                                     "calculation":{"emodulus medium":medium},
                                     "calculation":{"emodulus viscosity":viscosity},
                                     "calculation":{"emodulus temperature":temperature}
                                     })
        
        if medium == "Other":
            medium = viscosity

        for mm in self.analysis.measurements:
            # compute elastic modulus
            emod = dclab.elastic.get_elasticity(
                    area=mm.area_um,
                    deformation=mm.deform,
                    medium=medium,
                    channel_width=mm.config["general"]["channel width"],
                    flow_rate=mm.config["general"]["flow rate [ul/s]"],
                    temperature=temperature)
            mm.emodulus=emod
            
            for key in ["kde accuracy emodulus", "contour accuracy emodulus"]:
                if key in mm.config["plotting"]: 
                    mm.config["plotting"].pop(key)
        
        self.analysis._complete_config()
        self.funcparent.OnChangeFilter()


    def UpdatePanel(self, analysis=None):
        if analysis is None:
            analysis = self.analysis
        self.analysis = analysis

        self.ClearSubPanel()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        statbox = self.make_emodulus_choices(analysis)
        sizer.Add(statbox)
        
        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerv)
        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
