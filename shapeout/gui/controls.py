#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - control panels

"""
from __future__ import division, print_function

import numpy as np
import tempfile
import warnings
import webbrowser

import wx
import wx.grid as gridlib
import wx.lib.flatnotebook as fnb
import wx.lib.agw.hypertreelist as HT
from wx.lib.scrolledpanel import ScrolledPanel

from ..configuration import ConfigurationFile
from .polygonselect import LineDrawerWindow
from .. import tlabwrap
from .. import util
from .. import lin_mix_mod


class FlatNotebook(wx.Notebook):
    """
    Flatnotebook class
    """
    def __init__(self, parent):
        """Constructor"""
        style = fnb.FNB_RIBBON_TABS|\
                fnb.FNB_TABS_BORDER_SIMPLE|fnb.FNB_NO_X_BUTTON|\
                fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NODRAG
        # Bugfix for Mac
        #if platform.system().lower() in ["windows", "linux"]:
        #    style = style|fnb.FNB_HIDE_ON_SINGLE_TAB
        self.fnb = wx.Notebook.__init__(self, parent, wx.ID_ANY,
                                             )#agwStyle=style)


class ControlPanel(ScrolledPanel):
    """"""
    def __init__(self, parent, frame):
        """Constructor"""
        ScrolledPanel.__init__(self, parent)
        self.SetupScrolling(scroll_y=True)
        self.SetupScrolling(scroll_x=True)
        
        self.frame = frame
        self.config = frame.config
        self.notebook = FlatNotebook(self)

        self.subpanels = []

        self.AddSubpanels()
        
        self.notebook.SetSelection(4)

        # Shortucut SHIFT+ENTER replots everything
        randomId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnChangePlot, id=randomId)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT, wx.WXK_RETURN, randomId )])
        self.SetAcceleratorTable(accel_tbl)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)


    def AddSubpanels(self):
        notebook=self.notebook
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
        notebook.AddPage(self.page_plot, _("Plotting"))
        self.subpanels.append(self.page_plot)
        
        self.page_scat = SubPanelPlotScatter(notebook, funcparent=self)
        notebook.AddPage(self.page_scat, _("Scatter Plot"))
        self.subpanels.append(self.page_scat)

        self.page_cont = SubPanelPlotContour(notebook, funcparent=self)
        notebook.AddPage(self.page_cont, _("Contour Plot"))
        self.subpanels.append(self.page_cont)


    def NewAnalysis(self, anal=None):
        # destroy everything on Info panel and replot.
        if anal is not None:
            self.analysis = anal
            
        self.UpdatePages()
        
    
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
        wait = wx.BusyCursor()
        
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
                var = name
                if isinstance(c, wx.ComboBox) and hasattr(c, "data"):
                    # handle combobox selections such that the string in the
                    # combobox does not matter, only the selection id.
                    cid = c.GetSelection()
                    if cid != -1:
                        val = c.data[cid]
                    else:
                        val = c.GetValue()
                else:
                    val = c.GetValue()

                var,val = tlabwrap.dfn.MapParameterStr2Type(var, val)
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
        
        del wait


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
        sel = self.notebook.GetSelection()

        # Recreate all pages instead of just calling `UpdatePanel`.
        # This resolves issues on at least Linux
        for _i in range(len(self.subpanels)):
            self.notebook.RemovePage(0)
        self.subpanels = []
        self.AddSubpanels()

        # Update page content        
        for page in self.subpanels:
            page.UpdatePanel(self.analysis)
            # workaround to force redrawing of Page:
            page.Layout()
            page.Refresh()
            page.Update()
            
        # select previously selected page
        self.notebook.SetSelection(sel)
        self.notebook.Refresh()
        self.notebook.Update()


class DragListStriped(wx.ListCtrl):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._onDrag)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onSelect)
        self.Bind(wx.EVT_LEFT_UP,self._onMouseUp)
        self.Bind(wx.EVT_LEFT_DOWN, self._onMouseDown)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._onLeaveWindow)
        self.Bind(wx.EVT_ENTER_WINDOW, self._onEnterWindow)
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self._onInsert)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self._onDelete)

        #---------------
        # Variables
        #---------------
        self.IsInControl=True
        self.startIndex=-1
        self.dropIndex=-1
        self.IsDrag=False
        self.dragIndex=-1

    def _onLeaveWindow(self, event):
        self.IsInControl=False
        self.IsDrag=False
        event.Skip()

    def _onEnterWindow(self, event):
        self.IsInControl=True
        event.Skip()

    def _onDrag(self, event):
        self.IsDrag=True
        self.dragIndex=event.m_itemIndex
        event.Skip()
        pass

    def _onSelect(self, event):
        self.startIndex=event.m_itemIndex
        event.Skip()

    def _onMouseUp(self, event):
        # Purpose: to generate a dropIndex.
        # Process: check self.IsInControl, check self.IsDrag, HitTest, compare HitTest value
        # The mouse can end up in 5 different places:
        # Outside the Control
        # On itself
        # Above its starting point and on another item
        # Below its starting point and on another item
        # Below its starting point and not on another item

        if self.IsInControl==False:       #1. Outside the control : Do Nothing
            self.IsDrag=False
        else:                                   # In control but not a drag event : Do Nothing
            if self.IsDrag==False:
                pass
            else:                               # In control and is a drag event : Determine Location
                self.hitIndex=self.HitTest(event.GetPosition())
                self.dropIndex=self.hitIndex[0]
                # -- Drop index indicates where the drop location is; what index number
                #---------
                # Determine dropIndex and its validity
                #--------
                if self.dropIndex==self.startIndex or self.dropIndex==-1:    #2. On itself or below control : Do Nothing
                    pass
                else:
                    #----------
                    # Now that dropIndex has been established do 3 things
                    # 1. gather item data
                    # 2. delete item in list
                    # 3. insert item & it's data into the list at the new index
                    #----------
                    dropList=[]         # Drop List is the list of field values from the list control
                    thisItem=self.GetItem(self.startIndex)
                    for x in range(self.GetColumnCount()):
                        dropList.append(self.GetItem(self.startIndex,x).GetText())
                    thisItem.SetId(self.dropIndex)
                    self.DeleteItem(self.startIndex)
                    self.InsertItem(thisItem)
                    for x in range(self.GetColumnCount()):
                        self.SetStringItem(self.dropIndex,x,dropList[x])
            #------------
            # I don't know exactly why, but the mouse event MUST
            # call the stripe procedure if the control is to be successfully
            # striped. Every time it was only in the _onInsert, it failed on
            # dragging index 3 to the index 1 spot.
            #-------------
            # Furthermore, in the load button on the wxFrame that this lives in,
            # I had to call the _onStripe directly because it would occasionally fail
            # to stripe without it. You'll notice that this is present in the example stub.
            # Someone with more knowledge than I probably knows why...and how to fix it properly.
            #-------------
        self._onStripe()
        self.IsDrag=False
        event.Skip()

    def _onMouseDown(self, event):
        self.IsInControl=True
        event.Skip()

    def _onInsert(self, event):
        # Sequencing on a drop event is:
        # wx.EVT_LIST_ITEM_SELECTED
        # wx.EVT_LIST_BEGIN_DRAG
        # wx.EVT_LEFT_UP
        # wx.EVT_LIST_ITEM_SELECTED (at the new index)
        # wx.EVT_LIST_INSERT_ITEM
        #--------------------------------
        # this call to onStripe catches any addition to the list; drag or not
        self._onStripe()
        self.dragIndex=-1
        event.Skip()

    def _onDelete(self, event):
        self._onStripe()
        event.Skip()

    def _onStripe(self):
        if self.GetItemCount()>0:
            for x in range(self.GetItemCount()):
                if x % 2==0:
                    self.SetItemBackgroundColour(x,wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT))
                else:
                    self.SetItemBackgroundColour(x,wx.WHITE)



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
        choices = tlabwrap.dfn.GetParameterChoices(key, item[0],
                                                ignore_axes=ignore_axes)

        if len(choices) != 0:
            if choices[0] in tlabwrap.dfn.axlabels:
                human_choices = [ _(tlabwrap.dfn.axlabels[c]) for c in choices]
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

        elif (tlabwrap.dfn.GetParameterDtype(key, item[0]) == bool or  # @UndefinedVariable
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
            axeslist = [tlabwrap.dfn.axlabels[a] for a in self.axes]
            self.WXCB_axes = wx.ComboBox(self, -1, choices=axeslist,
                                    value=_("None"), name="None",
                                    style=wx.CB_DROPDOWN|wx.CB_READONLY)
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
            sizer_bag.Add(wx.StaticText(self, label=_("Treatment")), (1,1), span=wx.GBSpan(1,1))
            sizer_bag.Add(wx.StaticText(self, label=_("Repetition")), (1,2), span=wx.GBSpan(1,1))
            
            treatments = [_("None"), _("Control")] + [_("Treatment {}").format(i) for i in range(1,5)]
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

            hbox.Add(sizer_bag)
            
        return hbox
    
    def OnApply(self, e=None):
        """
        Perfrom LME4 computation
        """
        # Get axis name
        axname = self.axes[self.WXCB_axes.GetSelection()]
        # Get axis property
        axprop = tlabwrap.dfn.cfgmaprev[axname]
        
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

    def UpdatePanel(self, analysis=None):
        if analysis is None:
            analysis = self.analysis
        self.analysis = analysis

        for item in self.GetChildren():
            item.Hide()
            self.RemoveChild(item)
            item.Destroy()
        
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
        self.UpdatePanel()

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


class SubPanelInfo(SubPanel):
    def __init__(self, *args, **kwargs):
        SubPanel.__init__(self, *args, **kwargs)

    def UpdatePanel(self, analysis):
        """  """
        for item in self.GetChildren():
            item.Hide()
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

        # Determine the order in which things are displayed
        # in the control panel
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
        
        useditems = []
        ## Populate axes
        for item in items:
            if (item[0].startswith("Axis") or 
                item[0].startswith("Scale ")):
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
                stemp.Add(a, 0, wx.ALIGN_CENTER_VERTICAL)
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

    def _box_order_plots(self, analysis):
        """Returns a sizer containing a StaticBox that allows
        to sort the plots.
        """
        meas_names = [mm.title for mm in analysis.measurements]

        box = wx.StaticBox(self, label=_("Plot order"))

        dls = DragListStriped(box, style=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_NO_HEADER)
        dls.InsertColumn(0, "")
        dls.InsertColumn(1, "")

        for ii, meas in enumerate(meas_names):
            dls.InsertStringItem(ii, str(ii))
            dls.SetStringItem(ii, 1, meas)
            
        dls._onStripe()

        size = dls.GetBestSize()        
        dls.SetSize((size[0]-120,size[1]-50))
        
        dls.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        dls.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        
        self.plot_orderer = dls
        
        return box


    def OnApply(self, e=None):
        """ Apply the settings set by the user.
        We are allowing the user to order the plots, which we
        take care of here. 
        """
        # Order the plots according to user selection
        # find order
        order = []
        for ii in range(self.plot_orderer.GetItemCount()):
            order.append(int(self.plot_orderer.GetItem(ii).GetText()))
        # set order
        self.analysis.measurements = [x for (_y,x) in sorted(zip(
                                                order,
                                                self.analysis.measurements))]
        
        # Call OnChangePlot to apply the other changes
        self.funcparent.OnChangePlot(e)


    def UpdatePanel(self, analysis):
        """  """
        for item in self.GetChildren():
            item.Hide()
            self.RemoveChild(item)
            item.Destroy()

        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._box_from_cfg_plotting(analysis))
        sizer.Add(self._box_order_plots(analysis))


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
        
        self.analysis = analysis


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


    def UpdatePanel(self, analysis):
        """  """
        for item in self.GetChildren():
            item.Hide()
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


    def UpdatePanel(self, analysis):
        """  """
        for item in self.GetChildren():
            item.Hide()
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



class SubPanelStatistics(SubPanel):
    def __init__(self, *args, **kwargs):
        SubPanel.__init__(self, *args, **kwargs)

    def _box_statistics(self, analysis):
        """
        Returns a wxBoxSizer with statistics information about
        each element in analysis.
        """
        #gen = wx.StaticBox(self, label=_("Filtered data sets"))
        sizer = wx.BoxSizer(wx.VERTICAL)

        if analysis is not None:
            colors = list()
            for mm in analysis.measurements:
                colors.append(mm.Configuration["Plotting"]["Contour Color"])
            
            head, datalist = analysis.GetStatisticsBasic()
             
            myGrid = gridlib.Grid(self)
            myGrid.CreateGrid(len(datalist), len(head)-1)

            sizer.Add(myGrid, 1, wx.EXPAND)
            
            for ii, label in enumerate(head[1:]):
                myGrid.SetColLabelValue(ii, label)
                myGrid.SetColSize(ii, 10*len(label))

            for jj, row, color in zip(range(len(datalist)), datalist, colors):
                if analysis.GetParameters("Plotting")["Scatter Title Colored"]:
                    if isinstance(color, (list, tuple)):
                        color = util.rgb_to_hex(color[:3], norm=1)
                else:
                    color = "black"
                for ii, item in enumerate(row):
                    if isinstance(item, (str, unicode)):
                        label = u" {} ".format(item)
                    else:
                        label = u" {} ".format(util.float2string_nsf(item, n=3))
                    if ii is 0:
                        myGrid.SetRowLabelValue(jj, label)
                        oldsize = myGrid.GetRowLabelSize()
                        newsize = len(label)*10
                        myGrid.SetRowLabelSize(max(oldsize, newsize))
                    else:
                        myGrid.SetCellValue(jj, ii-1, label)
                        myGrid.SetCellTextColour(jj, ii-1, color)
                        myGrid.SetReadOnly(jj, ii-1)
            sizer.Layout()
        return sizer


    def UpdatePanel(self, analysis):
        """  """
        for item in self.GetChildren():
            item.Hide()
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


# These lists name items that belong to separate pages, startsiwth(item)
Plotting_Elements_Contour = ["Contour", "KDE"]
Plotting_Elements_Scatter = ["Downsampl", "Scatter"] # Downsampl [sic]
