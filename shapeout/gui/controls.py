#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - control panels
"""
from __future__ import division, print_function

import numpy as np

import wx
import wx.grid as gridlib
from wx.lib.scrolledpanel import ScrolledPanel

import dclab
from dclab import config as dc_config

from .. import tlabwrap
from .. import util


from . import plot_scatter
from . import plot_contour

from .controls_subpanel import SubPanel
from .controls_analysis import SubPanelAnalysis
from .controls_filtering import SubPanelFilter
from .controls_info import SubPanelInfo
from .controls_scatterplot import SubPanelPlotScatter, Plotting_Elements_Scatter
from .controls_contourplot import SubPanelPlotContour, Plotting_Elements_Contour



class FlatNotebook(wx.Notebook):
    """
    Flatnotebook class
    """
    def __init__(self, parent):
        """Constructor"""
        self.fnb = wx.Notebook.__init__(self, parent, wx.ID_ANY)


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
        
        # Only update the plotting data.
        # (Until version 0.6.1 the plots were recreated after
        #  each update, which caused a memory leak)
        plot_window = self.frame.PlotArea.mainplot.plot_window
        plots = plot_window.component.components
        for plot in plots:
            for mm in self.analysis.measurements:
                if plot.id == mm.identifier:
                    plot_scatter.set_scatter_data(plot, mm)
                    plot_scatter.reset_inspector(plot)
            
            if plot.id == "ShapeOut_contour_plot":
                plot_contour.set_contour_data(plot, self.analysis.measurements)


        self.UpdatePages()
        wx.EndBusyCursor()
    

    def OnChangePlot(self, e=None):
        # Set plot order
        if hasattr(self.analysis, "measurements"):
            mms = [ self.analysis.measurements[ii] for ii in self.page_plot.plot_order ]
            # make sure that we don't miss any new measurements on the way.
            newmeas = len(self.analysis.measurements) - len(mms)
            if newmeas > 0:
                mms += self.analysis.measurements[-newmeas:]
            self.analysis.measurements = mms
        
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

                var, val = dc_config.map_config_value_str2type(var, val)
                newfilt[var] = val
            elif name.startswith("Title "):
                # Change title of measurement
                for mm in self.analysis.measurements:
                    if mm.identifier == name[len("Title "):]:
                        mm.title = c.GetValue()
            elif name.startswith("Color "):
                # Change plotting color of measurement
                for mm in self.analysis.measurements:
                    if mm.identifier == name[len("Title "):]:
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
        dclab.PolygonFilter(points=result["points"],
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

    def _box_order_plots(self, analysis, sizex=300, sizey=150):
        """Returns a sizer containing a StaticBox that allows
        to sort the plots.
        """
        meas_names = [mm.title for mm in analysis.measurements]

        box = wx.StaticBox(self, label=_("Plot order"))
        statboxsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        dls = DragListStriped(box,
                              style=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_NO_HEADER|wx.EXPAND,
                              size=(sizex, sizey))
        dls.InsertColumn(0, "")
        dls.InsertColumn(1, "")

        for ii, meas in enumerate(meas_names):
            dls.InsertStringItem(ii, str(ii))
            dls.SetStringItem(ii, 1, meas)
            
        dls._onStripe()
        
        dls.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        dls.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        
        self.plot_orderer = dls

        statboxsizer.Add(dls)

        return statboxsizer


    @property
    def plot_order(self):
        order = []
        for ii in range(self.plot_orderer.GetItemCount()):
            order.append(int(self.plot_orderer.GetItem(ii).GetText()))
        return order


    def OnApply(self, e=None):
        """ Apply the settings set by the user.
        """
        # Call OnChangePlot to apply the other changes
        self.funcparent.OnChangePlot(e)


    def UpdatePanel(self, analysis):
        """  """
        self.ClearSubPanel()

        # sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        plotsizer = self._box_from_cfg_plotting(analysis)
        ordersizer = self._box_order_plots(analysis, sizey=plotsizer.GetMinSize()[1]-25)
        ordersizer.SetMinSize((-1, plotsizer.GetMinSize()[1]))

        sizer.Add(plotsizer)
        sizer.Add(ordersizer)

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
        self.ClearSubPanel()
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


