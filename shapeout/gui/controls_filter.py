#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import dclab
import wx
import wx.lib.agw.hypertreelist as HT

from dclab.definitions import feature_name2label

from ..settings import SettingsFile
from ..session import conversion
from .polygonselect import LineDrawerWindow
from .controls_subpanel import SubPanel

class SubPanelFilter(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = SettingsFile()
        self.key = "Filtering"

    def _box_rest_filter(self, analysis, key):
        """
        Display rest like data event limit
        """
        gen = wx.StaticBox(self, label="Other filters")

        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        items = analysis.GetParameters(key).items()

        sortfunc = lambda x: (x[0].replace("max", "2")
                                  .replace("min", "1"))
        items.sort(key=sortfunc)
        
        
        sgen = wx.FlexGridSizer(len(items), 1)
        
        excludeend = ["min", "max"]
        excludeis = ["enable filters"]
        excludestart = ["polygon", "hierarchy"]
        
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


    def _box_hierarchy_filter(self, analysis, key):
        """
        Display hierarchy filtering elements
        """
        gen = wx.StaticBox(self, label="Filter Hierarchy")

        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        sgen = wx.GridBagSizer()
        explanation = "Filter hierarchies can be used to apply\n"+\
        "multiple filters in sequence or to\n"+\
        "compare subpopulations in a data set."
        sgen.Add(wx.StaticText(self, label=explanation), (0,0), span=(1,2))
        sgen.Add(wx.StaticText(self, label="Select data set"+": "), (1,0),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        items = self.analysis.GetTitles()
        self.WXCOMBO_hparent = wx.ComboBox(self, choices=items)
        sgen.Add(self.WXCOMBO_hparent, (1,1)) 
        self.WXCOMBO_hparent.Bind(wx.EVT_COMBOBOX, self.OnHierarchySelParent)
        
        sgen.Add(wx.StaticText(self, label="Hierarchy parent"+": "), (2,0))
        self.WXTextHParent = wx.StaticText(self, label="")
        sgen.Add(self.WXTextHParent, (2,1), flag=wx.EXPAND)

        self.WXbtnnew = wx.Button(self, wx.ID_ANY, label="Create hierarchy child")
        sgen.Add(self.WXbtnnew, (3,0), span=(1,2), flag=wx.EXPAND)
        self.WXbtnnew.Bind(wx.EVT_BUTTON, self.OnHierarchyCreateChild)

        sgen.Layout()
        hbox.Add(sgen)

        if len(items):
            self.WXCOMBO_hparent.SetSelection(0)
            self.OnHierarchySelParent()
        return hbox


    def _box_minmax_filter(self, analysis, key):
        """
        Display everything with Min/Max
        """
        gen = wx.StaticBox(self, label="Box Filters")

        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)
        
        items = analysis.GetParameters(key).items()

        sortfunc = lambda x: (x[0].replace("max", "2")
                                  .replace("min", "1"))
        items.sort(key=sortfunc)
        
        sgen = wx.FlexGridSizer(len(items), 2)

        for item in items:
            if item[0].endswith("min"):
                if item[0][:-4] in analysis.GetUnusableAxes():
                    # ignore this item
                    continue
                # find item with max
                feat = item[0][:-4]
                idmax = [ii[0] for ii in items].index(feat+" max")
                itemmax = items[idmax]
                a = wx.StaticText(self, label="Range "+feat)
                b = wx.TextCtrl(self, value=str(item[1]), name=item[0])
                b.SetToolTip(wx.ToolTip("Minimum "+feature_name2label[feat]))
                c = wx.TextCtrl(self, value=str(itemmax[1]), name=itemmax[0])
                c.SetToolTip(wx.ToolTip("Maximum "+feature_name2label[feat]))
                stemp = wx.BoxSizer(wx.HORIZONTAL)
                sgen.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
                stemp.Add(b)
                stemp.Add(c)
                sgen.Add(stemp)

            elif item[0].endswith("max"):
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
        #  invert
        #  delete
        #  import
        #  export       preview plot
        #  export all   (own axis w/ label)
        polybox = wx.StaticBox(self, name="",
                               label="Polygon Filters")
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
        new = wx.Button(self, label="New")
        new.Bind(wx.EVT_BUTTON, self.OnPolygonWindow)
        optsizer.Add(new)
        # duplicate
        duplicate = wx.Button(self, label="Duplicate")
        duplicate.Bind(wx.EVT_BUTTON, self.OnPolygonDuplicate)
        optsizer.Add(duplicate)
        # edit
        invert = wx.Button(self, label="Invert")
        invert.Bind(wx.EVT_BUTTON, self.OnPolygonInvert)
        optsizer.Add(invert)

        # remove
        remove = wx.Button(self, label="Remove")
        remove.Bind(wx.EVT_BUTTON, self.OnPolygonRemove)
        optsizer.Add(remove)
        # import
        imp = wx.Button(self, label="Import")
        imp.Bind(wx.EVT_BUTTON, self.OnPolygonImport)
        optsizer.Add(imp)
        
        ## right column
        # dropdown (plot selection)
        choice_be = analysis.GetTitles()
        cbg = wx.ComboBox(self, -1, choices=choice_be,
                                value="None", name="None",
                                style=wx.CB_DROPDOWN|wx.CB_READONLY)
        if choice_be:
            cbg.SetSelection(len(choice_be) - 1)
            cbg.SetValue(choice_be[-1])
        cbg.Bind(wx.EVT_COMBOBOX, self.OnPolygonCombobox)
        plotsizer.Add(cbg)

        # htree control for polygon filter selection
        pol_filters = dclab.PolygonFilter.instances

        htreectrl = HT.HyperTreeList(self, name="Polygon Filter Selection",
                agwStyle=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|\
                         HT.TR_NO_HEADER|HT.TR_EDIT_LABELS)
        htreectrl.DeleteAllItems()
        # We are setting names as editable here. However, we cannot do any
        # event handling here, so we can only change the name in the underlying 
        # dclab.polygon_filter instance at certain function calls. That should
        # be enough, though. Use self..
        htreectrl.AddColumn("", edit=True)
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
        export = wx.Button(self, label="Export")
        export.Bind(wx.EVT_BUTTON, self.OnPolygonExport)
        horsizer2.Add(export)
        # export_all
        export_all = wx.Button(self, label="Export All")
        export_all.Bind(wx.EVT_BUTTON, self.OnPolygonExportAll)
        horsizer2.Add(export_all)
        plotsizer.Add(horsizer2)
        
        self._polygon_filter_combo_box = cbg
        self._polygon_filter_selection_htree = htreectrl

        self.OnPolygonCombobox()
        return polysizer


    def _set_polygon_filter_names(self):
        """
        Set the polygon filter names from the UI in the underlying
        dclab.polygon_filter classes.
        
         
        """
        # get selection from htree
        ctrls = self.GetChildren()
        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            if c.GetName() == "Polygon Filter Selection":
                # get the selected items
                r = c.GetRootItem()
                for ch in r.GetChildren():
                    # get the name.
                    name = ch.GetText()
                    unique_id = ch.GetData()
                    p = dclab.PolygonFilter.get_instance_from_id(unique_id)
                    p.name = name
            

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


    def OnHierarchyCreateChild(self, e=None):
        """
        Called when the user wants to create a new hierarchy child.
        Will create a new RT-DC dataset that is appended to
        `self.analysis`.
        In the end, the entire control panel is updated to give the
        user access to the new data set.
        """
        self._set_polygon_filter_names()
        sel = self.WXCOMBO_hparent.GetSelection()
        mm = self.analysis[sel]
        ds = dclab.new_dataset(mm)
        self.analysis.append(ds)
        self.funcparent.OnChangePlot()

    def OnHierarchySelParent(self, e=None):
        """
        Called when an RT-DC dataset is selected in the combobox.
        This methods updates the label of `self.WXTextHParent`. 
        """
        sel = self.WXCOMBO_hparent.GetSelection()
        mm = self.analysis[sel]
        hp = mm.config["filtering"]["hierarchy parent"]
        if hp.lower() == "none":
            label = "no parent"
        else:
            label = mm.hparent.title
        self.WXTextHParent.SetLabel(label)
    

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
        mm = self.analysis[sel]
        # get filters
        r = htreectrl.GetRootItem()
        if "polygon filters" in mm.config["filtering"]:
            filterlist = mm.config["filtering"]["polygon filters"]
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
        self._set_polygon_filter_names()
        _c, ch = self.GetPolygonHtreeSelected()
        if ch is None:
            return
        unique_id = ch.GetData()
        p = dclab.PolygonFilter.get_instance_from_id(unique_id)
        dclab.PolygonFilter(points=p.points,
                            axes=p.axes,
                            name=p.name+" (copy)")
        self.UpdatePanel()


    def OnPolygonExport(self, e=None, export_all=False):
        self._set_polygon_filter_names()
        if not export_all:
            _c, ch = self.GetPolygonHtreeSelected()
            if ch is None:
                return
        dlg = wx.FileDialog(self, "Open polygon file",
                    self.config.get_path(name="Polygon"), "",
                    "Shape-Out polygon file (*.poly)|*.poly", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath().encode("utf-8")
            self.config.set_path(dlg.GetDirectory(),
                                            name="Polygon")
            dlg.Destroy()
        else:
            self.config.set_path(dlg.GetDirectory(),
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
        self._set_polygon_filter_names()
        if len(dclab.PolygonFilter.instances) != 0:
            self.OnPolygonExport(export_all=True)


    def OnPolygonHtreeChecked(self, e=None):
        """
        This function is called when an item in the htreectrl is checked
        or unchecked. We apply the corresponding filters to the underlying
        RT-DC data set live.
        ComboBox:: self._polygon_filter_combo_box
        HTreeCtrl: self._polygon_filter_selection_htree
        """
        htreectrl = self._polygon_filter_selection_htree
        cmb = self._polygon_filter_combo_box
        
        # get selection
        sel = cmb.GetSelection()
        # get measurement
        mm = self.analysis[sel]
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
        mm.config["filtering"]["polygon filters"] = newfilterlist
        
    
    def OnPolygonImport(self, e=None):
        dlg = wx.FileDialog(self, "Open polygon file",
                    self.config.get_path(name="Polygon"), "",
                    "Shape-Out polygon file (*.poly)|*.poly", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath().encode("utf-8")
            self.config.set_path(dlg.GetDirectory(),
                                 name="Polygon")
            dlg.Destroy()
        else:
            self.config.set_path(dlg.GetDirectory(),
                                 name="Polygon")
            dlg.Destroy()
            return # nothing more to do here
        if not fname.endswith(".poly"):
            fname += ".poly"
        # Convert polygon filters from old exports
        newfname = conversion.convert_polygon(infile=fname)
        dclab.PolygonFilter.import_all(newfname)
        self.UpdatePanel()
        # cleanup
        os.remove(newfname)


    def OnPolygonInvert(self, e=None):
        self._set_polygon_filter_names()
        _c, ch = self.GetPolygonHtreeSelected()
        if ch is None:
            return
        unique_id = ch.GetData()
        p = dclab.PolygonFilter.get_instance_from_id(unique_id)
        dclab.PolygonFilter(points=p.points,
                            axes=p.axes,
                            name=p.name+" (inverted)",
                            inverted=(not p.inverted),
                            )
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
        idn = self._polygon_filter_combo_box.GetSelection()
        if idn < 0:
            idn = 0

        xax, yax = self.analysis.GetPlotAxes()
        mm = self.analysis[idn]
        ldw.show_scatter(mm, xax=xax, yax=yax)
        ldw.Show()


    def UpdatePanel(self, analysis=None):
        if analysis is None:
            # previous analysis is used
            analysis = self.analysis
        if hasattr(self, "_polygon_filter_combo_box"):
            old_meas_selection = self._polygon_filter_combo_box.GetSelection()
        else:
            old_meas_selection = 0

        self.analysis = analysis
        
        self.ClearSubPanel()

        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Box filters
        fbox = self._box_minmax_filter(analysis, "Filtering")
        sizer.Add(fbox)
        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerv)
        # Polygon filters
        polysizer = self._box_polygon_filter(analysis)
        sizerv.Add(polysizer)

        # Hierarchy filters:
        rbox = self._box_hierarchy_filter(analysis, "Filtering")
        sizerv.Add(rbox)
        # Rest filters:
        rbox = self._box_rest_filter(analysis, "Filtering")
        sizerv.Add(rbox)
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
        filten = analysis.GetParameters("filtering")["enable filters"]
        cb = self._create_type_wx_controls(analysis,
                                           "Filtering",
                                           ["enable filters", filten],)
        vertsizer.Add(cb)
        btn_apply = wx.Button(self, label="Apply")
        ## TODO:
        # write function in this class that gives ControlPanel a new
        # analysis, such that OnChangeFilter becomes shorter.
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangeFilter, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label="Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)
        # Set the previously selected measurement
        self._polygon_filter_combo_box.SetSelection(old_meas_selection)
        # Make the htree control below the combobox aware of this selection
        self.OnPolygonCombobox()

        sizer.Add(vertsizer)

        self.BindEnableName(ctrl_source="limit events auto",
                            value=False,
                            ctrl_targets=["limit events"])
        self.SetSizer(sizer)
        sizer.Fit(self)
