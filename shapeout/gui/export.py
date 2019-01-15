#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - classes and methods for data export"""
from __future__ import division, print_function, unicode_literals

import io
import os

import dclab
import numpy as np
import wx
from wx.lib.scrolledpanel import ScrolledPanel


class ExportAnalysisEvents(wx.Frame):
    def __init__(self, parent, analysis, ext="ext", non_scalars=[]):
        self.parent = parent
        self.analysis = analysis
        self.ext = ext
        self.toggled_event_features = True
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Export all event data",
            pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## panel
        self.panel = ScrolledPanel(self)
        self.panel.SetupScrolling()
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        # init
        textinit = wx.StaticText(self.panel,
                    label="Export all event data as *.{} files.".format(ext))
        self.topSizer.Add(textinit)
        # Chechbox asking for Mono-Model
        horsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.WXCheckFilter = wx.CheckBox(self.panel,
         label="export filtered data only")
        self.WXCheckFilter.SetValue(True)
        horsizer.Add(self.WXCheckFilter, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        horsizer.AddStretchSpacer()
        # Button to (de)select all variables
        btnselect = wx.Button(self.panel, wx.ID_ANY, "(De-)select all")
        self.Bind(wx.EVT_BUTTON, self.OnToggleAllEventFeatures, btnselect)
        horsizer.Add(btnselect, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.topSizer.Add(horsizer, 0, wx.EXPAND)
        ## Add checkboxes
        checks = []
        # find out which are actually used in the analysis
        for cc in dclab.dfn.scalar_feature_names:
            for mm in self.analysis.measurements:
                if cc in mm:
                    checks.append(cc)
        checks = non_scalars + sorted(list(set(checks)))
        self.box = wx.StaticBox(self.panel, label="Axes")
        self.sizerin = wx.StaticBoxSizer(self.box, wx.VERTICAL)
        # get longest text of checks
        dc = wx.ScreenDC()
        tl = np.max([ dc.GetTextExtent(c)[0] for c in checks ])
        sp = dc.GetTextExtent(" ")[0]
        
        for c in checks:
            # label id (b/c of sorting)
            lid = c+":"+" "*((tl-dc.GetTextExtent(c)[0])//sp)+"\t"
            label = dclab.dfn.feature_name2label[c]
            cb = wx.CheckBox(self.panel, label=lid + label, name=c)
            self.sizerin.Add(cb)
            if c in self.analysis.GetPlotAxes():
                cb.SetValue(True)
        self.topSizer.Add(self.sizerin)
        btnbrws = wx.Button(self.panel, wx.ID_ANY, "Save to directory")
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, btnbrws)
        self.topSizer.Add(btnbrws, 0, wx.EXPAND)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.SetMinSize((self.topSizer.GetMinSizeTuple()[0], 500))
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)

    def OnBrowse(self, e=None):
        """ Let the user select a directory and save
        everything in that directory.
        """
        # warn the user, if there are measurements that
        # have the same name.
        names = [ m.title for m in self.analysis.measurements ]
        dupl = list(set([n for n in names if names.count(n) > 1]))
        if len(dupl) != 0:
            dlg1 = wx.MessageDialog(self,
                message="Cannot export plots with duplicate titles: {}".format(
                            ", ".join(dupl))\
                        +"\nPlot titles can be edited in the 'Contour Plot' tab.",
                style=wx.OK|wx.ICON_ERROR)
            if dlg1.ShowModal() == wx.ID_OK:
                return

        # make directory dialog
        dlg2 = wx.DirDialog(self,
                           message="Select directory for data export",
                           defaultPath=self.parent.config.get_path("ExportData"),
                           style=wx.DD_DEFAULT_STYLE)
        
        if dlg2.ShowModal() == wx.ID_OK:
            outdir = dlg2.GetPath().encode("utf-8")
            self.parent.config.set_path(outdir, "ExportData")
            
            # determine if user wants filtered data
            filtered = self.WXCheckFilter.IsChecked()

            # search all children for checkboxes that have
            # the names in dclab.dfn.feature_names
            names = dclab.dfn.feature_names
            features = []
            for ch in self.panel.GetChildren():
                if (isinstance(ch, wx._controls.CheckBox) and 
                    ch.IsChecked()):
                    name = ch.GetName()
                    if name in names:
                        features.append(name)
            
            # Call the export function of dclab.rtdc_dataset
            # Check if the files already exist
            for m in self.analysis.measurements:
                if os.path.exists(os.path.join(outdir, m.title+"."+self.ext)):
                    msg = "Override existing .{} files in '{}'?".format(
                                                           self.ext, outdir)
                    dlg3 = wx.MessageDialog(self,
                                message=msg,
                                style=wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
                    if dlg3.ShowModal() == wx.ID_YES:
                        # ok, leave loop
                        break
                    else:
                        # do not continue
                        return
            wx.BeginBusyCursor()
            self.export(out_dir=outdir, features=features, filtered=filtered)
            wx.EndBusyCursor()
            
    def OnToggleAllEventFeatures(self, e=None):
        """Set all values of the event features to 
        `self.toggled_event_features` and invert
        `self.toggled_event_features`.
        """
        panel = self.panel
        names = dclab.dfn.feature_names
        for ch in panel.GetChildren():
            if (isinstance(ch, wx._controls.CheckBox) and 
                ch.GetName() in names):
                ch.SetValue(self.toggled_event_features)
            
        # Invert for next execution
        self.toggled_event_features = not self.toggled_event_features

    @staticmethod
    def get_dataset_features(data_set, features):
        out_feat = []
        for feat in features:
            if feat in data_set:
                out_feat.append(feat)
        return out_feat

    def export(self, out_dir, features, filtered):
        raise NotImplementedError("Please subclass and rewrite this function.")



class ExportAnalysisEventsFCS(ExportAnalysisEvents):
    def __init__(self, parent, analysis):
        super(ExportAnalysisEventsFCS, self).__init__(parent,
                                                      analysis,
                                                      ext="fcs")

    def export(self, out_dir, features, filtered):
        for m in self.analysis.measurements:
            mfeat = self.get_dataset_features(m, features)
            m.export.fcs(os.path.join(out_dir, m.title+".fcs"),
                         mfeat,
                         filtered=filtered,
                         override=True)


class ExportAnalysisEventsRTDC(ExportAnalysisEvents):
    def __init__(self, parent, analysis):
        super(ExportAnalysisEventsRTDC, self).__init__(parent,
                                                       analysis,
                                                       ext="rtdc",
                                                       non_scalars=["contour",
                                                                    "image",
                                                                    "mask",
                                                                    "trace"])

    def export(self, out_dir, features, filtered):
        for m in self.analysis.measurements:
            mfeat = self.get_dataset_features(m, features)
            m.export.hdf5(os.path.join(out_dir, m.title+".rtdc"),
                          mfeat,
                          filtered=filtered,
                          override=True)


class ExportAnalysisEventsTSV(ExportAnalysisEvents):
    def __init__(self, parent, analysis):
        super(ExportAnalysisEventsTSV, self).__init__(parent,
                                                      analysis,
                                                      ext="tsv")

    def export(self, out_dir, features, filtered):
        for m in self.analysis.measurements:
            mfeat = self.get_dataset_features(m, features)
            m.export.tsv(os.path.join(out_dir, m.title+".tsv"),
                         mfeat,
                         filtered=filtered,
                         override=True)



def export_event_images_avi(parent, analysis):
    dlg = wx.DirDialog(parent,
               message="Select directory for video export",
               defaultPath=parent.config.get_path("ExportAVI"),
               style=wx.DD_DEFAULT_STYLE)
    if dlg.ShowModal() == wx.ID_OK:
        out_dir=dlg.GetPath().encode("utf-8")
        parent.config.set_path(out_dir, "ExportAVI")
        for m in analysis.measurements:
            m.export.avi(os.path.join(out_dir, m.title+".avi"),
                         override=True)


def export_event_image_png(parent, image):
    dlg = wx.FileDialog(parent, "Choose file to save",
                        parent.config.get_path("ExportEventPNG"),
                        "",
                        "Portable Network Graphics (*.png)|*.png;*.PNG",
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath().encode("utf-8")
        parent.config.set_path(os.path.dirname(path), "ExportEventPNG")
        if not path.lower().endswith(".png"):
            path += ".png"
        image.save(path)


def export_statistics_tsv(parent):
    # Get data
    head, data = parent.analysis.GetStatisticsBasic()
    exp = []
    # Format data
    exp.append("#"+"\t".join(head))
    for subd in data:
        subdnew = list()
        for d in subd:
            if isinstance(d, (str, unicode)):
                subdnew.append(d.replace("\t", " "))
            else:
                subdnew.append("{:.5e}".format(d))
        exp.append("\t".join(subdnew))
    for i in range(len(exp)):
        exp[i] += "\n\r"
    # File dialog
    
    dlg = wx.FileDialog(parent, "Choose file to save",
            parent.config.get_path("TSV"),
            "", "Tab separated file (*.tsv)|*.tsv;*.TSV",
            wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    # user cannot do anything until he clicks "OK"
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath().encode("utf-8")
        if path.lower().endswith(".tsv") is not True:
            path = path+".tsv"
        parent.config.set_path(os.path.dirname(path), "TSV")
        with io.open(path, 'w') as fd:
            fd.writelines(exp)

