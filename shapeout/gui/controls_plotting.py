#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - plotting control"""
from __future__ import division, print_function, unicode_literals

import wx

from .controls_subpanel import SubPanel
from .controls_scatterplot import Plotting_Elements_Scatter
from .controls_contourplot import Plotting_Elements_Contour


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

        axes = wx.StaticBox(self, label="Axes")
        axesbox = wx.StaticBoxSizer(axes, wx.VERTICAL)
        axessizer = wx.BoxSizer(wx.VERTICAL)
        axesbox.Add(axessizer)
        mastersizer.Add(axesbox)
        
        misc = wx.StaticBox(self, label="Miscellaneous")
        miscbox = wx.StaticBoxSizer(misc, wx.VERTICAL)
        miscsizer = wx.BoxSizer(wx.VERTICAL)
        miscbox.Add(miscsizer)
        mastersizer.Add(miscbox)

        items = analysis.GetParameters(key).items()
        # Determine the order in which things are displayed
        # in the control panel
        sortfunc = lambda x: (x[0].replace("max", "2")
                                  .replace("min", "1")
                                  .replace("plot", "1")
                                  .replace("accuracy", "2")
                                  .replace("columns", "a1")
                                  .replace("rows", "a2")
                                  .replace("axis", "Aa")
                                  .replace("fix range", "scale a"))
        
        items.sort(key=sortfunc)
        
        # distinguish between deformation and circularity
        display_circ = False
        if "circ" in analysis.GetPlotAxes():
            display_circ = True
            if "deform" in analysis.GetPlotAxes():
                display_circ = False
        
        xax, yax = analysis.GetPlotAxes()

        # Remove all items that have nothing to do with this page
        dellist = []
        exclude = Plotting_Elements_Scatter+Plotting_Elements_Contour
        for item in items:
            for stid in exclude:
                if item[0].startswith(stid):
                    dellist.append(item)
        for it in dellist:
            items.remove(it)
        
        # Remove unneccessary controls
        for topic in ["min", "max"]:
            dellist = []
            for item in items:
                if (item[0].endswith(topic) and
                   not (item[0] == "{} {}".format(xax, topic) or 
                        item[0] == "{} {}".format(yax, topic))):
                    dellist.append(item)
                elif display_circ and item[0] == "defo {}".format(topic):
                    dellist.append(item)
                elif not display_circ and item[0] == "circ {}".format(topic):
                    dellist.append(item)
            for it in dellist:
                items.remove(it)
        
        useditems = []
        ## Populate axes
        for item in items:
            if (item[0].startswith("axis") or 
                item[0].startswith("scale ") or
                item[0] == "fix range"):
                stemp = self._create_type_wx_controls(analysis, key, item)
                useditems.append(item)
                axessizer.Add(stemp)
            elif item[0].endswith("min"):
                # find item with max
                idmax = [ii[0] for ii in items].index(item[0][:-3]+"max")
                itemmax = items[idmax]
                a = wx.StaticText(self, label="Range "+item[0][:-4])
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
            if item[0].startswith("contour") or item[0].startswith("kde"):
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

        box = wx.StaticBox(self, label="Plot order")
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

        btn_apply = wx.Button(self, label="Apply")
        self.Bind(wx.EVT_BUTTON, self.OnApply, btn_apply)
        vertsizer.Add(btn_apply)

        btn_reset = wx.Button(self, label="Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)
        vertsizer.Add(btn_reset)

        sizer.Add(vertsizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
                
        self.analysis = analysis
