#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - wx measurement explorer"""
from __future__ import division, print_function


import numpy as np
import warnings
import wx
import wx.lib.agw.hypertreelist as HT
from wx.lib.scrolledpanel import ScrolledPanel


from .. import meta_tool

class ExplorerPanel(ScrolledPanel):
    """"""
    def __init__(self, parent, frame, col_width=400):
        """Constructor
        
        You can also use the function `self.BindAnalyze` to determine
        where the data file list goes.
        
        Use the method `self.SetProjectTree` to display projects.
        
        """
        wx.Panel.__init__(self, parent)
        self.frame = frame
        # Parameters important to determine size of htree control
        # (not important for one-column mode, just use something large)
        self.s_mult = 10
        self.s_off = 55
        self.col_width = col_width

        self.treelist = []
        
        # Set up box
        box = wx.StaticBox(self, label="Measurement browser")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        # Load tree control
        self.htreectrl = HT.HyperTreeList(self, 
                agwStyle=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|\
                         wx.TR_ROW_LINES|HT.TR_AUTO_CHECK_CHILD|\
                         HT.TR_AUTO_CHECK_PARENT|HT.TR_NO_HEADER)

        sizer.Add(self.htreectrl, 1, wx.EXPAND, 3)
        
        self.btn_selall = wx.Button(self, label="Select all")
        self.btn_selnon = wx.Button(self, label="Deselect all")
        # to add more butons, use 
        # wx.NewId and give it to the buttons as second argument
        # -> buttons can be identified with this id from the event
        self.btn_selflow1 = wx.Button(self, label="-")
        self.btn_selflow2 = wx.Button(self, label="-")
        self.btn_selflow3 = wx.Button(self, label="-")
        self.btn_add = wx.Button(self, label="Analyze")
        
        self.sizer_bag = wx.GridBagSizer()
        # Set size of buttons
        maxs = max(self.btn_selall.GetSize(), self.btn_selnon.GetSize())
        self.btn_selall.SetMinSize((maxs[0]*1.5, maxs[1]))
        self.btn_selnon.SetMinSize((maxs[0]*1.5, maxs[1]))
        self.btn_selflow1.SetMinSize(maxs)
        self.btn_selflow2.SetMinSize(maxs)
        self.btn_selflow3.SetMinSize(maxs)
        self.btn_add.SetMinSize((maxs[0]*2, maxs[1]))
        
        self.sizer_bag.Add(self.btn_selall,(0,0), span=wx.GBSpan(1,3))
        self.sizer_bag.Add(self.btn_selnon,(0,3), span=wx.GBSpan(1,3))
        self.sizer_bag.Add(self.btn_selflow1,(1,0), span=wx.GBSpan(1,2))
        self.sizer_bag.Add(self.btn_selflow2,(1,2), span=wx.GBSpan(1,2))
        self.sizer_bag.Add(self.btn_selflow3,(1,4), span=wx.GBSpan(1,2))
        self.sizer_bag.Add(self.btn_add,(2,1), span=wx.GBSpan(1,4))
    
        minsize = self.sizer_bag.GetMinSize()
        box.SetMinSize(minsize)
        
        self.normal_width = box.GetMinSize()[0]+10
        
        sizer.Add(self.sizer_bag)
        self.SetSizer(sizer)        

        # sets self.flowrates
        self.Update()
        
        self.Bind(wx.EVT_BUTTON, self.OnSelectAll, self.btn_selall)
        self.Bind(wx.EVT_BUTTON, self.OnSelectNone, self.btn_selnon)
        self.Bind(wx.EVT_BUTTON, self.OnSelectFlow1, self.btn_selflow1)
        self.Bind(wx.EVT_BUTTON, self.OnSelectFlow2, self.btn_selflow2)
        self.Bind(wx.EVT_BUTTON, self.OnSelectFlow3, self.btn_selflow3)
        self.Bind(wx.EVT_BUTTON, self.OnAnalyze, self.btn_add)
        
        self.BindAnalyze(lambda x: None)
        
        self.Disable()
        

    def BindAnalyze(self, func):
        self.external_analyze = func

    def CheckData(self, data=[]):
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                if k.GetData() in data:
                    k.Check(True)

    def BoldifyData(self, data=[]):
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                if k.GetData() in data:
                    k.SetBold(True)

    def external_analyze(self, *args, **kwargs):
        """ to be overridden """
        pass

    def OnAnalyze(self, e=None):
        """  
        - calls self.external_analyze with the list of data files
        - Updates bold font faces on tree view
        """
        files = []
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                if k.IsChecked():
                    k.SetBold(True)
                    files.append(k.GetData())
                else:
                    k.SetBold(False)
        self.htreectrl.SetColumnWidth(0, self.col_width)
        if files:
            self.external_analyze(files)
        else:
            raise ValueError("No data selected in Measurement Browser!")

    def OnSelectAll(self, e=None):
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            self.htreectrl.CheckItem(c)

    def OnSelectFlow1(self, e=None):
        self.OnSelectNone()
        frate = self.flowrates[0]
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                f = k.GetData()
                if ( not meta_tool.get_chip_region(f).lower() == "reservoir"
                     and frate == meta_tool.get_flow_rate(f) ):

                    self.htreectrl.CheckItem(k)


    def OnSelectFlow2(self, e=None):
        self.OnSelectNone()
        frate = self.flowrates[1]
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                f = k.GetData()
                if ( not meta_tool.get_chip_region(f).lower() == "reservoir"
                     and frate == meta_tool.get_flow_rate(f) ):
                    self.htreectrl.CheckItem(k)        


    def OnSelectFlow3(self, e=None):
        self.OnSelectNone()
        frate = self.flowrates[2]
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                f = k.GetData()
                if ( not meta_tool.get_chip_region(f).lower() == "reservoir"
                     and frate == meta_tool.get_flow_rate(f) ):
                    self.htreectrl.CheckItem(k)  


    def OnSelectNone(self, e=None):
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            self.htreectrl.CheckItem(c, False)

    def SelectData(self, data=[]):
        r = self.htreectrl.GetRootItem()
        for c in r.GetChildren():
            for k in c.GetChildren():
                if k.GetData() in data:
                    self.htreectrl.CheckItem(k)

    def SetProjectTree(self, data, add=False, marked=[]):
        """Update tree view with measurement data information

        Parameters
        ----------
        data : tuple (treelist, cols)
            The return value of `meta_tool.collect_data_tree`.
        add : bool
            If True, the current treelist is updated with new
            measurements. If False, the current treelist is replaced.
        """
        treelist, cols = data
        
        if add:
            # update treelist
            # check if already in tree
            for item in self.treelist:
                if not item in treelist:
                    treelist.append(item)

        # Any checked or bold items ?
        checked = []
        bold = marked
        r = self.htreectrl.GetRootItem()
        if r is not None:
            for c in r.GetChildren():
                for k in c.GetChildren():
                    f = k.GetData()
                    if k.IsBold():
                        bold.append(f)
                    if k.IsChecked():
                        checked.append(f)
        
        self.treelist = treelist

        # enable or disable window
        if len(self.treelist) == 0:
            self.Disable()
        else:
            self.Enable()

        # Clear first
        self.htreectrl.DeleteAllItems()

        # define column lengths
        col_width = 10
        
        for _i in range(self.htreectrl.GetColumnCount()):
            self.htreectrl.RemoveColumn(0)
            
        self.htreectrl.AddColumn(cols[0])

        rroot = self.htreectrl.AddRoot("", ct_type=0)

        # Add projects to tree
        for j in range(len(treelist)):
            project = treelist[j]
            root = self.htreectrl.AppendItem(rroot, project[0][0],
                                             ct_type=1,
                                             data=project[0][1])
            for k in range(1,len(project)):
                self.htreectrl.AppendItem(root, project[k][0],
                                          ct_type=1,
                                          data=project[k][1])
                # displayed column width
                col_width = max(len(project[k][0]), col_width)
        
        # Add warning message
        if len(treelist) == 0:
            msg = "No measurements found."
            root = self.htreectrl.AppendItem(rroot, msg, ct_type=0)
            col_width = max(len(msg), col_width)

        # Set size in htree control
        self.htreectrl.SetColumnWidth(0, self.col_width)
        #                              col_width*self.s_mult+self.s_off)
        self.htreectrl.ExpandAll()
        self.BoldifyData(bold)
        self.CheckData(checked)
        self.Update()


    def SetProjectTreeAdd(self, data):
        """ Convenience wrapper around SetProjectTree with True `add`"""
        self.SetProjectTree(data, add=True)


    def Update(self, e=None):
        """ Updates this panel (e.g. dis-/enables buttons)
        
        sets self.flowrates
        """
        self.btn_selall.Disable()
        self.btn_selnon.Disable()
        self.btn_selflow1.Disable()
        self.btn_selflow2.Disable()
        self.btn_selflow3.Disable()
        self.btn_add.Disable()
        self.btn_selflow1.SetLabel(u"-")
        self.btn_selflow2.SetLabel(u"-")
        self.btn_selflow3.SetLabel(u"-")
        
        self.flowrates=list()
        
        if len(self.treelist) != 0:
            self.btn_selall.Enable()
            self.btn_selnon.Enable()
            self.btn_add.Enable()
            
            flr=list()
            # get list of flow rates
            for item in self.treelist:
                # First tree item contains path to measurements
                for meas in item[1:]:
                    flr.append(meta_tool.get_flow_rate(meas[1]))
            flr = np.unique(flr)
            flr.sort()

            if len(flr) >= 1:
                self.btn_selflow1.SetLabel(u"{:.5f} µls⁻¹".format(flr[0]))
                self.btn_selflow1.Enable()
            if len(flr) >= 2:
                self.btn_selflow2.SetLabel(u"{:.5f} µls⁻¹".format(flr[1]))
                self.btn_selflow2.Enable()
            if len(flr) >= 3:
                self.btn_selflow3.SetLabel(u"{:.5f} µls⁻¹".format(flr[2]))
                self.btn_selflow3.Enable()
            if len(flr) > 3:
                warnings.warn("Only using first three flowrates!")
            self.flowrates = flr

