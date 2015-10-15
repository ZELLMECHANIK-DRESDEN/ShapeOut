#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - control panels

"""
from __future__ import division, print_function

import numpy as np
import platform
import wx

import wx.lib.agw.flatnotebook as fnb
import wx.lib.agw.hypertreelist as HT
from wx.lib.scrolledpanel import ScrolledPanel

from ..configuration import ConfigurationFile
from .polygonselect import LineDrawerWindow
from .. import tlabwrap
from .. import util

class FlatNotebook(fnb.FlatNotebook):
    """
    Flatnotebook class
    """
    def __init__(self, parent):
        """Constructor"""
        style = fnb.FNB_RIBBON_TABS|\
                fnb.FNB_TABS_BORDER_SIMPLE|fnb.FNB_NO_X_BUTTON|\
                fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NODRAG
        # Bugfix for Mac
        if platform.system().lower() in ["windows", "linux"]:
            style = style|fnb.FNB_HIDE_ON_SINGLE_TAB
        self.fnb = fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY,
                                             agwStyle=style)


class ControlPanel(ScrolledPanel):
    """"""
    def __init__(self, parent, frame):
        """Constructor"""
        ScrolledPanel.__init__(self, parent)
        self.SetupScrolling(scroll_y=True)
        self.SetupScrolling(scroll_x=True)
        
        self.frame = frame
        self.config = frame.config
        notebook = FlatNotebook(self) 

        self.subpanels = []

        page_info = SubPanelInfo(notebook)
        notebook.AddPage(page_info, _("Information"))
        self.subpanels.append(page_info)
        self.page_info = page_info
        
        self.page_filter = SubPanelFilter(notebook, funcparent=self)
        notebook.AddPage(self.page_filter, _("Filtering"))
        self.subpanels.append(self.page_filter)
        
        self.page_stat = SubPanelStatistics(notebook)
        notebook.AddPage(self.page_stat, _("Statistics"))
        self.subpanels.append(self.page_stat)
        
        self.page_cont = SubPanelAnalysis(notebook, funcparent=self)
        notebook.AddPage(self.page_cont, _("Analysis"))
        self.subpanels.append(self.page_cont)

        self.page_plot = SubPanelPlotting(notebook, funcparent=self)
        notebook.AddPage(self.page_plot, _("Plottting"))
        self.subpanels.append(self.page_plot)
        
        self.page_scat = SubPanelPlotScatter(notebook, funcparent=self)
        notebook.AddPage(self.page_scat, _("Scatter Plot"))
        self.subpanels.append(self.page_scat)

        self.page_cont = SubPanelPlotContour(notebook, funcparent=self)
        notebook.AddPage(self.page_cont, _("Contour Plot"))
        self.subpanels.append(self.page_cont)
        
        notebook.SetSelection(3)
        
        self.notebook = notebook
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)


    def NewAnalysis(self, anal=None):
        # destroy everything on Info panel and replot.
        if anal is not None:
            self.analysis = anal
            
        self.UpdatePages()
        
        # make the current page redraw itself
        self.notebook.SetSelection(self.notebook.GetSelection())

    
    def OnChangeFilter(self, e=None):
        # get all values
        wx.BeginBusyCursor()
        ctrls = self.page_filter.GetChildren()
        samdict = self.analysis.measurements[0].\
                                       Configuration["Filtering"].copy()
        newfilt = dict()

        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            name = c.GetName()
            if samdict.has_key(name):
                # box filters
                if isinstance(c, wx._controls.CheckBox):
                    newfilt[name] = bool(c.GetValue())
                else:
                    newfilt[name] = float(c.GetValue())

        chlist = self.page_filter.GetPolygonHtreeChecked()
        checked = []
        for ch in chlist:
            checked.append(ch.GetData())
        
        # Polygon filters are handled separately for each measurement.
        # This is done by the autobinding methods of the SubPanelFilter
        # - OnPolygonCombobox        (display filter for each mm)
        # - OnPolygonHtreeChecked    (change filter for each mm)
        #newfilt["Polygon Filters"] = checked
        
        cfg = { "Filtering" : newfilt }
        
        # Apply base data limits
        if cfg["Filtering"]["Limit Events Auto"]:
            minsize = self.analysis.ForceSameDataSize()
            cfg["Filtering"]["Limit Events"] = minsize
            for c in ctrls:
                name = c.GetName()
                if name == "Limit Events":
                    c.SetValue(str(minsize))
        
        self.analysis.SetParameters(cfg)
        
        # Update Plots
        self.frame.PlotArea.Plot(self.analysis)
        
        self.UpdatePages()
        wx.EndBusyCursor()
    

    def OnChangePlot(self, e=None):
        ctrls = list(self.page_plot.GetChildren())
        ctrls += list(self.page_cont.GetChildren())
        ctrls += list(self.page_scat.GetChildren())
        samdict = self.analysis.measurements[0].\
                                       Configuration["Plotting"].copy()
        newfilt = dict()
 
        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            name = c.GetName()
            if samdict.has_key(name):
                var,val = tlabwrap.dfn.MapParameterStr2Type(name,c.GetValue())  # @UndefinedVariable
                newfilt[var] = val
            elif "Title " in name:
                # Change title of measurement
                for mm in self.analysis.measurements:
                    if mm.identifier in name:
                        mm.title = c.GetValue()
            elif "Color " in name:
                # Change plotting color of measurement
                for mm in self.analysis.measurements:
                    if mm.identifier in name:
                        col = c.GetColour()
                        col = np.array([col.Red(), col.Green(),
                                       col.Blue(), col.Alpha()])/255
                        mm.Configuration["Plotting"]["Contour Color"] = col.tolist()
        
        cfg = { "Plotting" : newfilt }
        self.analysis.SetParameters(cfg)

        # Update Plots
        self.frame.PlotArea.Plot(self.analysis)
        self.UpdatePages()


    def OnPolygonFilter(self, result):
        """ Called by polygon Window """
        tlabwrap.PolygonFilter(points=result["points"],
                               axes=result["axes"])
        # update list of polygon filters
        self.UpdatePages()
        # The first polygon will be applied to all plots
        if len(self.page_filter.GetPolygonHtreeChecked()) == 0:
            ctrls = self.page_filter.GetChildren()
            # identify controls via their name correspondence in the cfg
            for c in ctrls:
                if c.GetName() == "Polygon Filter Selection":
                    # get the selected items
                    r = c.GetRootItem()
                    cs = r.GetChildren()
                    unique_id = cs[-1].GetData()
                    newcfg = {"Filtering": 
                              {"Polygon Filters": [unique_id]} }
                    self.analysis.SetParameters(newcfg)
            # and apply
            self.OnChangeFilter()


    def Reset(self, key, subkeys=[]):
        newcfg = tlabwrap.GetDefaultConfiguration(key)
        if len(subkeys) != 0:
            for k in list(newcfg.keys()):
                if not k in subkeys:
                    newcfg.pop(k)
        self.analysis.SetParameters({key : newcfg})
        if key == "Plotting" and "Contour Plot" in subkeys:
            self.analysis.SetContourAccuracies()
        self.UpdatePages()
        self.frame.PlotArea.Plot(self.analysis)
        

    def UpdatePages(self):
        """ fills pages """
        for page in self.subpanels:
            page.Update(self.analysis)



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
                sgen.Add(a)
                sgen.Add(b)
        
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
        choices = tlabwrap.dfn.GetParameterChoices(key, item[0],  # @UndefinedVariable
                                                ignore_axes=ignore_axes)
        if len(choices) != 0:
            a = wx.StaticText(self, label=_(item[0]))
            # sort choices with _()?
            c = wx.ComboBox(self, -1, choices=choices,
                            value=unicode(item[1]), name=item[0],
                            style=wx.CB_DROPDOWN|wx.CB_READONLY)
            if len(c.GetValue()) == 0:
                # comparison of floats and ints does not work
                for ch in choices:
                    if float(ch) == float(item[1]):
                        c.SetValue(ch)
            c.SetValue(unicode(item[1]))
            stemp.Add(a)
            stemp.Add(c)
        elif (tlabwrap.dfn.GetParameterDtype(key, item[0]) == bool or  # @UndefinedVariable
              str(item[1]).capitalize() in ["True", "False"]):
            a = wx.CheckBox(self, label=_(item[0]), name=item[0])
            a.SetValue(item[1])
            stemp.Add(a)
        else:
            a = wx.StaticText(self, label=_(item[0]))
            b = wx.TextCtrl(self, value=str(item[1]), name=item[0])
            stemp.Add(a)
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
            

    def Update(self, *args, **kwargs):
        """ Overwritten by subclass """
        pass


class SubPanelAnalysis(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.config = ConfigurationFile()
        self.key = "Analysis"

    def Update(self, analysis=None):
        if analysis is None:
            analysis = self.analysis
        self.analysis = analysis
        self.Freeze()
        
        for item in self.GetChildren():
            self.RemoveChild(item)
            item.Destroy()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerv)
        
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

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        
        self.Thaw()


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
                sgen.Add(a)
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
        pol_filters = tlabwrap.PolygonFilter.instances
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
        p = tlabwrap.PolygonFilter.get_instance_from_id(unique_id)
        tlabwrap.PolygonFilter(points=p.points, axes=p.axes)
        self.Update()

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
            p = tlabwrap.PolygonFilter.get_instance_from_id(unique_id)
            p.save(fname)
        else:
            # export all
            tlabwrap.PolygonFilter.save_all(fname)

    def OnPolygonExportAll(self, e=None):
        if len(tlabwrap.PolygonFilter.instances) != 0:
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
        tlabwrap.PolygonFilter.import_all(fname)
        self.Update()

    def OnPolygonRemove(self, e=None):
        c, ch = self.GetPolygonHtreeSelected()
        if ch is None:
            return
        unique_id = ch.GetData()
        tlabwrap.PolygonFilter.remove(unique_id)
        self.analysis.PolygonFilterRemove(unique_id)
        c.Delete(ch)
        self.funcparent.frame.PlotArea.Plot(self.analysis)

    def OnPolygonWindow(self, e=None):
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
        
    def Update(self, analysis=None):
        if analysis is None:
            analysis = self.analysis
        self.analysis = analysis
        self.Freeze()
        
        for item in self.GetChildren():
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

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        
        self.Thaw()


class SubPanelInfo(SubPanel):
    def __init__(self, *args, **kwargs):
        SubPanel.__init__(self, *args, **kwargs)

    def Update(self, analysis):
        """  """
        self.Freeze()
        for item in self.GetChildren():
            self.RemoveChild(item)
            item.Destroy()
        # Create three boxes containing information
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        genbox = self._box_from_cfg_read(analysis, "General")
        imbox = self._box_from_cfg_read(analysis, "Image")
        frbox = self._box_from_cfg_read(analysis, "Framerate")
        roibox = self._box_from_cfg_read(analysis, "ROI")
        # same size 
        h = genbox.GetMinSize()[1]
        h = max(h, imbox.GetMinSize()[1])
        h = max(h, frbox.GetMinSize()[1])
        h = max(h, roibox.GetMinSize()[1])
        h = max(h, 50)
        genbox.SetMinSize((-1, h))
        imbox.SetMinSize((-1, h))
        frbox.SetMinSize((-1, h))
        roibox.SetMinSize((-1, h))
        sizer.Add(genbox)
        sizer.Add(imbox)
        sizer.Add(frbox)
        sizer.Add(roibox)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Thaw()
        

class SubPanelPlotting(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.key = "Plotting"

    def _box_from_cfg_plotting(self, analysis):
        """ Top panel draw plotting elements
        """
        key = self.key 
        
        mastersizer = wx.BoxSizer(wx.HORIZONTAL)

        axes = wx.StaticBox(self, label=_("Axes"))
        axesbox = wx.StaticBoxSizer(axes, wx.VERTICAL)
        axessizer = wx.BoxSizer(wx.VERTICAL)
        axesbox.Add(axessizer)
        mastersizer.Add(axesbox)
        
        misc = wx.StaticBox(self, label=_("Miscellaneous"))
        miscbox = wx.StaticBoxSizer(misc, wx.VERTICAL)
        miscsizer = wx.BoxSizer(wx.VERTICAL)
        miscbox.Add(miscsizer)
        mastersizer.Add(miscbox)

        items = analysis.GetParameters(key).items()

        sortfunc = lambda x: (x[0].replace("Max", "2")
                                  .replace("Min", "1")
                                  .replace("Plot", "1")
                                  .replace("Accuracy", "2")
                                  .replace("Columns", "a1")
                                  .replace("Rows", "a2")
                                  .replace("Axis", "Aa"))
        
        items.sort(key=sortfunc)
        
        # distinguish between deformation and circularity
        display_circ = False
        if "Circ" in analysis.GetPlotAxes():
            display_circ = True
            if "Defo" in analysis.GetPlotAxes():
                display_circ = False
        
        xax, yax = analysis.GetPlotAxes()

        # Remove all items that have nothing to do with this page
        dellist = list()
        exclude = Plotting_Elements_Scatter+Plotting_Elements_Contour
        for item in items:
            for stid in exclude:
                if item[0].startswith(stid):
                    dellist.append(item)
        for it in dellist:
            items.remove(it)
        
        # Remove unneccessary controls
        for topic in ["Min", "Max"]:
            dellist = list()
            for item in items:
                if (item[0].endswith(topic) and
                   not (item[0] == "{} {}".format(xax, topic) or 
                        item[0] == "{} {}".format(yax, topic))):
                    dellist.append(item)
                elif display_circ and item[0] == "Defo {}".format(topic):
                    dellist.append(item)
                elif not display_circ and item[0] == "Circ {}".format(topic):
                    dellist.append(item)
            for it in dellist:
                items.remove(it)
        
        useditems = list()
        ## Populate axes
        for item in items:
            if item[0].startswith("Axis"):
                stemp = self._create_type_wx_controls(analysis, key, item)
                useditems.append(item)
                axessizer.Add(stemp)
            elif item[0].endswith("Min"):
                # find item with max
                idmax = [ii[0] for ii in items].index(item[0][:-3]+"Max")
                itemmax = items[idmax]
                a = wx.StaticText(self, label=_("Range "+item[0][:-4]))
                b = wx.TextCtrl(self, value=str(item[1]), name=item[0])
                c = wx.TextCtrl(self, value=str(itemmax[1]), name=itemmax[0])
                stemp = wx.BoxSizer(wx.HORIZONTAL)
                stemp.Add(a)
                stemp.Add(b)
                stemp.Add(c)
                axessizer.Add(stemp)
                useditems.append(item)
                useditems.append(itemmax)
        
        
        ## Contour plot is not here
        for item in items:
            if item[0].startswith("Contour") or item[0].startswith("KDE"):
                useditems.append(item)
                pass


        ## Populate misc
        for item in items:
            if not item in useditems:
                stemp = self._create_type_wx_controls(analysis, key, item)
                miscsizer.Add(stemp)

        # Set uniform size
        h = axesbox.GetMinSize()[1]
        h = max(h, miscbox.GetMinSize()[1])
        axesbox.SetMinSize((-1, h))
        miscbox.SetMinSize((-1, h))

        axessizer.Layout()
        miscsizer.Layout()
        mastersizer.Layout()
        
        return mastersizer

    def Update(self, analysis):
        """  """
        self.Freeze()
        for item in self.GetChildren():
            self.RemoveChild(item)
            item.Destroy()
        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        fbox = self._box_from_cfg_plotting(analysis)
        sizer.Add(fbox)

        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label=_("Apply"))
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangePlot, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        
        self.Thaw()



class SubPanelPlotContour(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.key = "Plotting"


    def _box_from_cfg_contour(self, analysis):
        """ Top panel draw plotting elements
        """
        key = self.key
        
        mastersizer = wx.BoxSizer(wx.HORIZONTAL)

        contour = wx.StaticBox(self, label=_("Parameters"))
        contourbox = wx.StaticBoxSizer(contour, wx.VERTICAL)
        contoursizer = wx.BoxSizer(wx.VERTICAL)
        contourbox.Add(contoursizer)
        mastersizer.Add(contourbox)

        items = analysis.GetParameters(key).items()
        # Remove individual contour color
        for item in items:
            if item[0] == "Contour Color":
                items.remove(item)
        
        # Remove all items that have nothing to do with plotting
        xax, yax = analysis.GetPlotAxes()
        for topic in ["KDE Multivariate", "Contour Accuracy"]:
            dellist = list()
            for item in items:
                if (item[0].startswith(topic) and
                   not (item[0].endswith(xax) or item[0].endswith(yax))):
                    dellist.append(item)
            for it in dellist:
                items.remove(it)

        ## Contour plot data
        items = tlabwrap.SortConfigurationKeys(items)
        for item in items:
            for strid in Plotting_Elements_Contour:
                if item[0].startswith(strid):
                    stemp = self._create_type_wx_controls(analysis, 
                                                          key, item)
                    contoursizer.Add(stemp)

        ## Color and name selection
        # ["Plotting"]["Contour Color"] and
        # mm.title
        titlecol = wx.StaticBox(self, label=_("Titles and Colors"))
        titlecolbox = wx.StaticBoxSizer(titlecol, wx.VERTICAL)
        titlecolsizer = wx.BoxSizer(wx.VERTICAL)
        titlecolbox.Add(titlecolsizer)
        mastersizer.Add(titlecolbox)
        
        for mm in analysis.measurements:
            shor = wx.BoxSizer(wx.HORIZONTAL)
            # title
            tit = wx.TextCtrl(self, value=str(mm.title), size=(300, -1),
                            name="Title "+mm.identifier)
            # color
            color = mm.Configuration["Plotting"]["Contour Color"]
            # convert tuple to wxColour
            if isinstance(color, list):
                color=wx.Colour(*np.array(color)*255)
            col = wx.ColourPickerCtrl(self, name="Color "+mm.identifier,
                                      col=color)
            shor.Add(col)
            shor.Add(tit)
            titlecolsizer.Add(shor)

        contourbox.SetMinSize((-1, contourbox.GetMinSize()[1]))
        contoursizer.Layout()
        titlecolsizer.Layout()
        mastersizer.Layout()
        
        return mastersizer


    def Update(self, analysis):
        """  """
        self.Freeze()
        for item in self.GetChildren():
            self.RemoveChild(item)
            item.Destroy()
        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        fbox = self._box_from_cfg_contour(analysis)
        sizer.Add(fbox)

        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label=_("Apply"))
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangePlot, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Thaw()



    
class SubPanelPlotScatter(SubPanel):
    def __init__(self, parent, *args, **kwargs):
        SubPanel.__init__(self, parent, *args, **kwargs)
        self.key = "Plotting"


    def _box_from_cfg_scatter(self, analysis):
        """ Top panel draw plotting elements
        """
        key = self.key
        
        mastersizer = wx.BoxSizer(wx.HORIZONTAL)

        scatter = wx.StaticBox(self, label=_("Parameters"))
        scatterbox = wx.StaticBoxSizer(scatter, wx.VERTICAL)
        scattersizer = wx.BoxSizer(wx.VERTICAL)
        scatterbox.Add(scattersizer)
        mastersizer.Add(scatterbox)

        items = analysis.GetParameters(key).items()

        ## Scatter plot data
        items = tlabwrap.SortConfigurationKeys(items)
        for item in items:
            for strid in Plotting_Elements_Scatter:
                if item[0].startswith(strid):
                    stemp = self._create_type_wx_controls(analysis, 
                                                          key, item)
                    scattersizer.Add(stemp)

        scatterbox.SetMinSize((-1, scatterbox.GetMinSize()[1]))

        scattersizer.Layout()
        mastersizer.Layout()
        
        return mastersizer


    def Update(self, analysis):
        """  """
        self.Freeze()
        for item in self.GetChildren():
            self.RemoveChild(item)
            item.Destroy()
        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        fbox = self._box_from_cfg_scatter(analysis)
        sizer.Add(fbox)

        vertsizer  = wx.BoxSizer(wx.VERTICAL)

        btn_apply = wx.Button(self, label=_("Apply"))
        self.Bind(wx.EVT_BUTTON, self.funcparent.OnChangePlot, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label=_("Reset"))
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Thaw()


class SubPanelStatistics(SubPanel):
    def __init__(self, *args, **kwargs):
        SubPanel.__init__(self, *args, **kwargs)

    def _box_statistics(self, analysis):
        """
        Returns a wxBoxSizer with statistics information about
        each element in analysis.
        """
        gen = wx.StaticBox(self, label=_("Filtered data sets"))
        hbox = wx.StaticBoxSizer(gen, wx.VERTICAL)

        if analysis is not None:

            
            colors = list()
            for mm in analysis.measurements:
                colors.append(mm.Configuration["Plotting"]["Contour Color"])
            
            head, datalist = analysis.GetStatisticsBasic()
            
            sgen = wx.FlexGridSizer(len(datalist)+1, len(datalist[0]))
            
            for label in head:
                ctrl = wx.StaticText(self, label=label)
                try:
                    ctrl.SetLabelMarkup("<b>{}</b>".format(label))
                except:
                    pass
                sgen.Add(ctrl)
                 
            
            for row, color in zip(datalist, colors):
                if isinstance(color, (list, tuple)):
                    color = util.rgb_to_hex(color[:3], norm=1)
                
                for item in row:
                    if isinstance(item, (str, unicode)):
                        label = u" {} ".format(item)
                    else:
                        label = u" {} ".format(util.float2string_nsf(item, n=3))
                    ctrl = wx.StaticText(self, label=label)
                    try:
                        ctrl.SetLabelMarkup("<span fgcolor='{}'>{}</span>".format(color, label))
                    except:
                        pass
                    sgen.Add(ctrl)
        
            sgen.Layout()
            hbox.Add(sgen)
        
        return hbox


    def Update(self, analysis):
        """  """
        self.Freeze()
        for item in self.GetChildren():
            self.RemoveChild(item)
            item.Destroy()
        # Create three boxes containing information
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        statbox = self._box_statistics(analysis)
        # same size 
        h = statbox.GetMinSize()[1]
        h = max(h, 50)
        statbox.SetMinSize((-1, h))
        sizer.Add(statbox)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Thaw()


# These lists name items that belong to separate pages, startsiwth(item)
Plotting_Elements_Contour = ["Contour", "KDE"]
Plotting_Elements_Scatter = ["Downsampl", "Scatter"]
