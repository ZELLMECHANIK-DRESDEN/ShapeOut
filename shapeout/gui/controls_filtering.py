#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import dclab
import wx
import wx.lib.agw.hypertreelist as HT

from .polygonselect import LineDrawerWindow
from ..configuration import ConfigurationFile

from .controls_subpanel import SubPanel

class SubPanelFilter(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = ConfigurationFile()
        self.key = "Filtering"

    def _box_rest_filter(self, analysis, key):
        """
        Display rest like data event limit
        """
        gen = wx.StaticBox(self, label=_("Other filters"))

        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        items = analysis.GetParameters(key).items()

        sortfunc = lambda x: (x[0].replace("Max", "2")
                                  .replace("Min", "1"))
        items.sort(key=sortfunc)
        
        
        sgen = wx.FlexGridSizer(len(items), 1)
        
        excludeend = ["Min", "Max"]
        excludeis = ["Enable Filters"]
        excludestart = ["Polygon"]
        
        #sgen = wx.BoxSizer(wx.VERTICAL)
        for item in items:
            ins = True
            for it in excludeend:
                if item[0].endswith(it):
                    ins = False
            for it in excludeis:
                if item[0] == it:
                    ins = False
            for it in excludestart:
                if item[0].startswith(it):
                    ins = False
            if not ins:
                continue
            stemp = self._create_type_wx_controls(analysis,
                                                  key, item)
            sgen.Add(stemp)

        sgen.Layout()
        hbox.Add(sgen)
        return hbox
    

    def _box_minmax_filter(self, analysis, key):
        """
        Display everything with Min/Max
        """
        gen = wx.StaticBox(self, label=_("Box Filters"))

        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        items = analysis.GetParameters(key).items()

        sortfunc = lambda x: (x[0].replace("Max", "2")
                                  .replace("Min", "1"))
        items.sort(key=sortfunc)
        
        
        sgen = wx.FlexGridSizer(len(items), 2)
        #sgen = wx.BoxSizer(wx.VERTICAL)
        
        # distinguish between deformation and circularity
        display_circ = False
        if "Circ" in analysis.GetPlotAxes():
            display_circ = True
            if "Defo" in analysis.GetPlotAxes():
                display_circ = False

        for item in items:
            if item[0].startswith("Circ") and display_circ is False:
                pass
            elif item[0].startswith("Defo") and display_circ is True:
                pass
            elif item[0].endswith("Min"):
                if item[0][:-4] in analysis.GetUnusableAxes():
                    # ignore this item
                    continue
                # find item with max
                idmax = [ii[0] for ii in items].index(item[0][:-3]+"Max")
                itemmax = items[idmax]
                a = wx.StaticText(self, label=_("Range "+item[0][:-4]))
                b = wx.TextCtrl(self, value=str(item[1]), name=item[0])
                c = wx.TextCtrl(self, value=str(itemmax[1]), name=itemmax[0])
                stemp = wx.BoxSizer(wx.HORIZONTAL)
                sgen.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
                stemp.Add(b)
                stemp.Add(c)
                sgen.Add(stemp)

            elif item[0].endswith("Max"):
                # did that before
                pass
            else:
                pass

        sgen.Layout()
        hbox.Add(sgen)
        
        return hbox

    def _box_polygon_filter(self, analysis):
        ## Polygon box
        # layout: 
        #  new          selection box
        #  duplicate    (multiple selections)
        #  edit
        #  delete
        #  import
        #  export       preview plot
        #  export all   (own axis w/ label)
        polybox = wx.StaticBox(self, name="",
                               label=_("Polygon Filters"))
        # sizers
        polysizer = wx.StaticBoxSizer(polybox, wx.HORIZONTAL)
        horsizer = wx.BoxSizer(wx.HORIZONTAL)
        optsizer = wx.BoxSizer(wx.VERTICAL)
        plotsizer = wx.BoxSizer(wx.VERTICAL)
        horsizer.Add(optsizer)
        horsizer.Add(plotsizer)
        polysizer.Add(horsizer)

        ## left column
        # new
        new = wx.Button(self, label=_("New"))
        new.Bind(wx.EVT_BUTTON, self.OnPolygonWindow)
        optsizer.Add(new)
        # duplicate
        duplicate = wx.Button(self, label=_("Duplicate"))
        duplicate.Bind(wx.EVT_BUTTON, self.OnPolygonDuplicate)
        optsizer.Add(duplicate)
        # edit
        edit = wx.Button(self, label=_("Edit"))
        #edit.Bind(wx.EVT_BUTTON, self.OnPolygonEdit)
        edit.Disable()
        optsizer.Add(edit)

        # remove
        remove = wx.Button(self, label=_("Remove"))
        remove.Bind(wx.EVT_BUTTON, self.OnPolygonRemove)
        optsizer.Add(remove)
        # import
        imp = wx.Button(self, label=_("Import"))
        imp.Bind(wx.EVT_BUTTON, self.OnPolygonImport)
        optsizer.Add(imp)
        
        ## right column
        # dropdown (plot selection)
        choice_be = analysis.GetTitles()
        cbg = wx.ComboBox(self, -1, choices=choice_be,
                                value=_("None"), name="None",
                                style=wx.CB_DROPDOWN|wx.CB_READONLY)
        cbg.SetSelection(min(0, len(choice_be)-1))
        cbg.SetValue(choice_be[-1])
        cbg.Bind(wx.EVT_COMBOBOX, self.OnPolygonCombobox)
        plotsizer.Add(cbg)

        # htree control for polygon filter selection
        pol_filters = dclab.PolygonFilter.instances

        htreectrl = HT.HyperTreeList(self, name="Polygon Filter Selection",
                agwStyle=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|\
                         HT.TR_NO_HEADER|HT.TR_EDIT_LABELS)
        htreectrl.DeleteAllItems()
        htreectrl.AddColumn("")
        htreectrl.SetColumnWidth(0, 500)
        rroot = htreectrl.AddRoot("", ct_type=0)

        for p in pol_filters:
            # filtit = 
            htreectrl.AppendItem(rroot, p.name, ct_type=1,
                                          data=p.unique_id)

        htreectrl.Bind(HT.EVT_TREE_ITEM_CHECKED, self.OnPolygonHtreeChecked)
        # This is covered by self.OnPolygonCombobox()
        #    FIL = analysis.GetParameters("Filtering")
        #    if (FIL.has_key("Polygon Filters") and
        #        p.unique_id in FIL["Polygon Filters"]):
        #        filtit.Check(True)
        htreectrl.SetMinSize((200,120))

        plotsizer.Add(htreectrl, 1, wx.EXPAND, 3)
        # export
        horsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        export = wx.Button(self, label=_("Export"))
        export.Bind(wx.EVT_BUTTON, self.OnPolygonExport)
        horsizer2.Add(export)
        # export_all
        export_all = wx.Button(self, label=_("Export All"))
        export_all.Bind(wx.EVT_BUTTON, self.OnPolygonExportAll)
        horsizer2.Add(export_all)
        plotsizer.Add(horsizer2)
        
        self._polygon_filter_combo_box = cbg
        self._polygon_filter_selection_htree = htreectrl

        self.OnPolygonCombobox()
        return polysizer

    def GetPolygonHtreeChecked(self):
        """ Returns
        """
        checked = list()
        # get selection from htree
        ctrls = self.GetChildren()
        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            if c.GetName() == "Polygon Filter Selection":
                # get the selected items
                r = c.GetRootItem()
                for ch in r.GetChildren():
                    if ch.IsChecked():
                        checked.append(ch)
        # else
        return checked

    def GetPolygonHtreeSelected(self):
        """ Returns
        """
        # get selection from htree
        ctrls = self.GetChildren()
        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            if c.GetName() == "Polygon Filter Selection":
                # get the selected items
                r = c.GetRootItem()
                for ch in r.GetChildren():
                    if ch.IsSelected():
                        return c, ch
        # else
        return c, None

    def OnPolygonCombobox(self, e=None):
        """
        Called when the user selects a different item in the plot selection
        combobox. We will mark the activated filters for that plot. in the
        selection box below.
        ComboBox:: self._polygon_filter_combo_box
        HTreeCtrl: self._polygon_filter_selection_htree
        """
        htreectrl = self._polygon_filter_selection_htree
        cmb = self._polygon_filter_combo_box
        
        # get selection
        sel = cmb.GetSelection()
        # get measurement
        mm = self.analysis.measurements[sel]
        # get filters
        r = htreectrl.GetRootItem()
        if "Polygon Filters" in mm.Configuration["Filtering"]:
            filterlist = mm.Configuration["Filtering"]["Polygon Filters"]
            #print(filterlist)
            # set visible filters
            for item in r.GetChildren():
                #print("looking at", item.GetData())
                if item.GetData() in filterlist:
                    #print("will check")
                    htreectrl.CheckItem(item, True)
                else:
                    #print("wont check")
                    htreectrl.CheckItem(item, False)
        else:
            # Uncheck everything, because mm does not know Filtering
            for item in r.GetChildren():
                htreectrl.CheckItem(item, False)
            

    def OnPolygonDuplicate(self, e=None):
        _c, ch = self.GetPolygonHtreeSelected()
        if ch is None:
            return
        unique_id = ch.GetData()
        p = dclab.PolygonFilter.get_instance_from_id(unique_id)
        dclab.PolygonFilter(points=p.points, axes=p.axes)
        self.UpdatePanel()

    def OnPolygonExport(self, e=None, export_all=False):
        if not export_all:
            _c, ch = self.GetPolygonHtreeSelected()
            if ch is None:
                return
        dlg = wx.FileDialog(self, "Open polygon file",
                    self.config.GetWorkingDirectory(name="Polygon"), "",
                    "ShapeOut polygon file (*.poly)|*.poly", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath()
            self.config.SetWorkingDirectory(dlg.GetDirectory(),
                                            name="Polygon")
            dlg.Destroy()
        else:
            self.config.SetWorkingDirectory(dlg.GetDirectory(),
                                            name="Polygon")
            dlg.Destroy()
            return # nothing more to do here
        if not fname.endswith(".poly"):
            fname += ".poly"
        if not export_all:
            unique_id = ch.GetData()
            p = dclab.PolygonFilter.get_instance_from_id(unique_id)
            p.save(fname)
        else:
            # export all
            dclab.PolygonFilter.save_all(fname)

    def OnPolygonExportAll(self, e=None):
        if len(dclab.PolygonFilter.instances) != 0:
            self.OnPolygonExport(export_all=True)

    def OnPolygonHtreeChecked(self, e=None):
        """
        This function is called when an item in the htreectrl is checked
        or unchecked. We apply the corresponding filters to the underlying
        RTDC data set live.
        ComboBox:: self._polygon_filter_combo_box
        HTreeCtrl: self._polygon_filter_selection_htree
        """
        htreectrl = self._polygon_filter_selection_htree
        cmb = self._polygon_filter_combo_box
        
        # get selection
        sel = cmb.GetSelection()
        # get measurement
        mm = self.analysis.measurements[sel]
        # get filters
        newfilterlist = list()
        
        # set visible filters
        r = htreectrl.GetRootItem()
        for item in r.GetChildren():
            if item.IsChecked():
                #print(item.GetData(), "checked")
                newfilterlist.append(item.GetData())
            else:
                #print(item.GetData(), "unhecked")
                pass
        # apply filters to data set
        mm.Configuration["Filtering"]["Polygon Filters"] = newfilterlist
        
    
    def OnPolygonImport(self, e=None):
        dlg = wx.FileDialog(self, "Open polygon file",
                    self.config.GetWorkingDirectory(name="Polygon"), "",
                    "ShapeOut polygon file (*.poly)|*.poly", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath()
            self.config.SetWorkingDirectory(dlg.GetDirectory(),
                                            name="Polygon")
            dlg.Destroy()
        else:
            self.config.SetWorkingDirectory(dlg.GetDirectory(),
                                            name="Polygon")
            dlg.Destroy()
            return # nothing more to do here
        if not fname.endswith(".poly"):
            fname += ".poly"
        dclab.PolygonFilter.import_all(fname)
        self.UpdatePanel()

    def OnPolygonRemove(self, e=None):
        c, ch = self.GetPolygonHtreeSelected()
        if ch is None:
            return
        unique_id = ch.GetData()
        dclab.PolygonFilter.remove(unique_id)
        self.analysis.PolygonFilterRemove(unique_id)
        c.Delete(ch)
        self.funcparent.frame.PlotArea.Plot(self.analysis)

    def OnPolygonWindow(self, e=None):
        """ Called when user wants to add a new polygon filter """
        ldw = LineDrawerWindow(self.funcparent,
                               self.funcparent.OnPolygonFilter)
        # get plot that we want to use
        name = self._polygon_filter_combo_box.GetValue()
        names = self.analysis.GetTitles()
        if name in names:
            idn = names.index(name)
        else:
            idn = 0

        xax, yax = self.analysis.GetPlotAxes()
        mm = self.analysis.measurements[idn]
        ldw.show_scatter(mm, xax=xax, yax=yax)
        ldw.Show()
        
    def UpdatePanel(self, analysis=None):
        if analysis is None:
            # previous analysis is used
            analysis = self.analysis
        if hasattr(self, "_polygon_filter_combo_box") :
            old_meas_selection = self._polygon_filter_combo_box.GetSelection()
        else:
            old_meas_selection = 0

        self.analysis = analysis
        
        for item in self.GetChildren():
            item.Hide()
            self.RemoveChild(item)
            item.Destroy()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerv)
        # Box filters
        fbox = self._box_minmax_filter(analysis, "Filtering")
        sizerv.Add(fbox)
        # Rest filters:
        rbox = self._box_rest_filter(analysis, "Filtering")
        sizerv.Add(rbox)
        
        # Polygon filters
        polysizer = self._box_polygon_filter(analysis)
        sizer.Add(polysizer)
        
        ## Polygon box
        # layout: 
        #  new          selection box
        #  duplicate    (multiple selections)
        #  edit
        #  delete
        #  import
        #  export       preview plot
        #  export all   (own axis w/ label)
        #
        ## Polygon selection
        # line_drawing example
        # - selection: choose which data to be displayed
        # - on press enter, draw polygon and allow new selection.
        # - buttons: add, clear, clear all
        # (- show other polygons with selection box)
        
        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        filten = analysis.GetParameters("Filtering")["Enable Filters"]
        cb = self._create_type_wx_controls(analysis,
                                           "Filtering",
                                           ["Enable Filters", filten],)
        vertsizer.Add(cb)

        btn_apply = wx.Button(self, label=_("Apply"))
        ## TODO:
        # write function in this class that gives ControlPanel a new
        # analysis, such that OnChangeFilter becomes shorter.
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangeFilter, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        # Set the previously selected measurement
        self._polygon_filter_combo_box.SetSelection(old_meas_selection)
        # Make the htree control below the combobox aware of this selection
        self.OnPolygonCombobox()

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
