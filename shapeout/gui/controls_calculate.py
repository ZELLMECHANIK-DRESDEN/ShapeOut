#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
import dclab
import tempfile
import webbrowser
import wx

from ..configuration import ConfigurationFile
from .. import lin_mix_mod, tlabwrap

from .controls_subpanel import SubPanel

class SubPanelCalculate(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = ConfigurationFile()
        self.key = "Calculate"

    
    def make_analysis_choices(self, analysis):
        gen = wx.StaticBox(self, label=_("Elastic modulus"))
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:
            # get common parameters
            sizer_bag = wx.GridBagSizer(hgap=20, vgap=5)

            # Model to apply
            sizer_bag.Add(wx.StaticText(self, label=_("Mixed effects model:")),
                          (0,0), span=wx.GBSpan(1,1))
            choices = tlabwrap.get_config_entry_choices("analysis",
                                                        "regression model")
            model=analysis.measurements[0].config["analysis"]["regression model"]
            self.WXCB_model = wx.ComboBox(self, -1, choices=choices,
                                    value=model, name="regression model",
                                    style=wx.CB_DROPDOWN|wx.CB_READONLY)
            sizer_bag.Add(self.WXCB_model, (0,1), span=wx.GBSpan(1,3))
            self.Bind(wx.EVT_COMBOBOX, self.update_info_text, self.WXCB_model)
            
            # Axis to analyze
            sizer_bag.Add(wx.StaticText(self, label=_("Axis to analyze:")), (1,0), span=wx.GBSpan(1,1))
            self.axes = analysis.GetUsableAxes()
            axeslist = [dclab.dfn.axlabels[a] for a in self.axes]
            self.WXCB_axes = wx.ComboBox(self, -1, choices=axeslist,
                                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
            self.Bind(wx.EVT_COMBOBOX, self.update_info_text, self.WXCB_axes)

            # Set y-axis as default
            ax = analysis.GetPlotAxes()[1]
            if ax in self.axes:
                axid = self.axes.index(ax)
            else:
                axid = 0
            self.WXCB_axes.SetSelection(axid)
            sizer_bag.Add(self.WXCB_axes, (1,1), span=wx.GBSpan(1,3))
            
            # Header for table
            sizer_bag.Add(wx.StaticText(self, label=_("Data set")), (2,0), span=wx.GBSpan(1,1))
            sizer_bag.Add(wx.StaticText(self, label=_("Interpretation")), (2,1), span=wx.GBSpan(1,1))
            sizer_bag.Add(wx.StaticText(self, label=_("Repetition")), (2,2), span=wx.GBSpan(1,1))
            
            treatments = ["None", "Control", "Treatment",
                          "Reservoir Control", "Reservoir Treatment"]
            repetitions = [str(i) for i in range(1,10)]
            
            self.WXCB_treatment = []
            self.WXCB_repetition = []
            
            for ii, mm in enumerate(analysis.measurements):
                # title
                sizer_bag.Add(wx.StaticText(self, label=mm.title), (3+ii,0), span=wx.GBSpan(1,1))
                # treatment
                cbgtemp = wx.ComboBox(self, -1, choices=treatments,
                                      name=mm.identifier,
                                      style=wx.CB_DROPDOWN|wx.CB_READONLY)
                if mm.title.lower().count("control") or ii==0:
                    cbgtemp.SetSelection(1)
                else:
                    cbgtemp.SetValue(mm.config["analysis"]["regression treatment"])
                sizer_bag.Add(cbgtemp, (3+ii,1), span=wx.GBSpan(1,1))
                # repetition
                cbgtemp2 = wx.ComboBox(self, -1, choices=repetitions,
                                      name=mm.identifier,
                                      style=wx.CB_DROPDOWN|wx.CB_READONLY)
                cbgtemp2.SetSelection(mm.config["analysis"]["regression repetition"]-1)
                

                sizer_bag.Add(cbgtemp2, (3+ii,2), span=wx.GBSpan(1,1))
                
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

        model = self.WXCB_model.GetValue()
        self.analysis.SetParameters({"analysis":{"regression model":model}})
        
        for ii, mm in enumerate(self.analysis.measurements):
            # get treatment (ignore 0)
            if self.WXCB_treatment[ii].GetSelection() == 0:
                # The user selected _("None")
                continue
            xs.append(getattr(mm, axprop)[mm._filter])
            mmtreat = self.WXCB_treatment[ii].GetValue()
            treatment.append(mmtreat)
            # get repetition
            mmrep = int(self.WXCB_repetition[ii].GetValue())
            timeunit.append(mmrep)
            
            # Set regression parameters
            mm.config["analysis"]["regression treatment"] = mmtreat
            mm.config["analysis"]["regression repetition"] = mmrep
        
        # run lme4
        result = lin_mix_mod.linmixmod(xs=xs,
                                       treatment=treatment,
                                       timeunit=timeunit,
                                       model=model)
        # display results
        # write to temporary file and display with webbrowser
        outf = tempfile.mktemp(prefix="regression_analysis_{}_".format(axprop),
                               suffix=".txt")
        with codecs.open(outf, "w", encoding="utf-8") as fd:
            fd.writelines(result["Full Summary"].replace("\n", "\r\n"))

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
        if self.WXCB_model.GetSelection() == 0:
            text_mode = _("Will compute linear mixed-effects model for {}.\n")
        elif self.WXCB_model.GetSelection() == 1:
            text_mode = _("Will compute generalized linear mixed-effects model for {}.\n")
        else:
            raise ValueError("Unsupported model selection")
        
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


        self.Bind(wx.EVT_BUTTON, self.OnApply, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
