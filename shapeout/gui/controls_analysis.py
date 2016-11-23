#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import dclab
import tempfile
import webbrowser
import wx

from ..configuration import ConfigurationFile
from .. import lin_mix_mod

from .controls_subpanel import SubPanel

class SubPanelAnalysis(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = ConfigurationFile()
        self.key = "Analysis"

    
    def make_analysis_choices(self, analysis):
        gen = wx.StaticBox(self, label=_("Linear mixed-effects model"))
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:
            # get common parameters
            sizer_bag = wx.GridBagSizer(hgap=20, vgap=5)
            
            sizer_bag.Add(wx.StaticText(self, label=_("Axis to analyze:")), (0,0), span=wx.GBSpan(1,1))
            
            # axes dropdown
            self.axes = analysis.GetUsableAxes()
            axeslist = [dclab.dfn.axlabels[a] for a in self.axes]
            self.WXCB_axes = wx.ComboBox(self, -1, choices=axeslist,
                                    value=_("None"), name="None",
                                    style=wx.CB_DROPDOWN|wx.CB_READONLY)
            self.Bind(wx.EVT_COMBOBOX, self.update_info_text, self.WXCB_axes)
            # Set y-axis as default
            ax = analysis.GetPlotAxes()[1]
            if ax in self.axes:
                axid = self.axes.index(ax)
            else:
                axid = 0
            self.WXCB_axes.SetSelection(axid)
            sizer_bag.Add(self.WXCB_axes, (0,1), span=wx.GBSpan(1,4))
            
            # Header for table
            sizer_bag.Add(wx.StaticText(self, label=_("Data set")), (1,0), span=wx.GBSpan(1,1))
            sizer_bag.Add(wx.StaticText(self, label=_("Interpretation")), (1,1), span=wx.GBSpan(1,1))
            sizer_bag.Add(wx.StaticText(self, label=_("Repetition")), (1,2), span=wx.GBSpan(1,1))
            
            treatments = [_("None"), _("Control"), _("Treatment"),
                          _("Reservoir Control"), _("Reservoir Treatment")]
            repetitions = [str(i) for i in range(1,10)]
            
            self.WXCB_treatment = []
            self.WXCB_repetition = []
            
            for ii, mm in enumerate(analysis.measurements):
                # title
                sizer_bag.Add(wx.StaticText(self, label=mm.title), (2+ii,0), span=wx.GBSpan(1,1))
                # treatment
                cbgtemp = wx.ComboBox(self, -1, choices=treatments,
                                      name=mm.identifier,
                                      style=wx.CB_DROPDOWN|wx.CB_READONLY)
                if mm.title.lower().count("control") or ii==0:
                    cbgtemp.SetSelection(1)
                else:
                    cbgtemp.SetSelection(0)
                sizer_bag.Add(cbgtemp, (2+ii,1), span=wx.GBSpan(1,1))
                # repetition
                cbgtemp2 = wx.ComboBox(self, -1, choices=repetitions,
                                      name=mm.identifier,
                                      style=wx.CB_DROPDOWN|wx.CB_READONLY)
                cbgtemp2.SetSelection(0)
                sizer_bag.Add(cbgtemp2, (2+ii,2), span=wx.GBSpan(1,1))
                
                self.WXCB_treatment.append(cbgtemp)
                self.WXCB_repetition.append(cbgtemp2)
                
                self.Bind(wx.EVT_COMBOBOX, self.update_info_text, cbgtemp2)
                self.Bind(wx.EVT_COMBOBOX, self.update_info_text, cbgtemp)

            hbox.Add(sizer_bag)
            self.info_text = wx.StaticText(self, label="")
            hbox.Add(self.info_text, wx.EXPAND)
            
        return hbox


    def OnApply(self, e=None):
        """
        Perfrom LME4 computation
        """
        # Get axis name
        axname = self.axes[self.WXCB_axes.GetSelection()]
        # Get axis property
        axprop = dclab.dfn.cfgmaprev[axname]
        
        # loop through analysis
        treatment = []
        timeunit = []
        xs = []
        
        for ii, mm in enumerate(self.analysis.measurements):
            # get treatment (ignore 0)
            if self.WXCB_treatment[ii].GetSelection() == 0:
                # The user selected _("None")
                continue
            xs.append(getattr(mm, axprop)[mm._filter])
            treatment.append(self.WXCB_treatment[ii].GetValue())
            # get repetition
            timeunit.append(int(self.WXCB_repetition[ii].GetValue()))
            
        # run lme4
        result = lin_mix_mod.linmixmod(xs=xs,
                                       treatment=treatment,
                                       timeunit=timeunit)
        # display results
        # write to temporary file and display with webbrowser
        with tempfile.NamedTemporaryFile(mode="w", prefix="linmixmod_", suffix=".txt", delete=False) as fd:
            fd.writelines(result["Full Summary"])
            
        webbrowser.open(fd.name)


    def OnReset(self, e=None):
        """
        Reset everything in the analysis tab.
        """
        self.UpdatePanel(self.analysis)


    def update_info_text(self, e=None):
        """ The info text helps the user a little bit selecting data.
        """
        text = ""
        axis = self.WXCB_axes.GetValue()
        # treatments
        trt = [ t.GetValue() for t in self.WXCB_treatment]
        # user selected reservoir somewhere
        resc = len([t for t in trt if t.count(_("Reservoir Control"))])
        rest = len([t for t in trt if t.count(_("Reservoir Treatment"))])
        text_mode = _("Will compute linear mixed-effects model for {}.\n")
        
        if not rest*resc and rest+resc:
            text += _("Please select reservoir for treatment and control.")
        elif resc+rest:
            text += text_mode.format("{} {}".format(_("differential"), axis))
            text += _(" - Will bootstrap channel/reservoir data.\n")
            text += _(" - Will perform {} bootstrapping iterations.\n".format(
                                                    lin_mix_mod.DEFAULT_BS_ITER))
        else:
            text += text_mode.format(axis)
        self.info_text.SetLabel(text)
        self.Layout()


    def UpdatePanel(self, analysis=None):
        if analysis is None:
            analysis = self.analysis
        self.analysis = analysis

        self.ClearSubPanel()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        statbox = self.make_analysis_choices(analysis)
        sizer.Add(statbox)
        
        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerv)
        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label=_("Apply"))
        ## TODO:
        # write function in this class that gives ControlPanel a new
        # analysis, such that OnChangeFilter becomes shorter.
        self.Bind(wx.EVT_BUTTON, self.OnApply, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
