#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - wx frontend components

"""
from __future__ import division, print_function, unicode_literals

import chaco.api as ca
import dclab
from enable.api import Window
import numpy as np
from PIL import Image

import wx
from wx.lib.scrolledpanel import ScrolledPanel


class ImagePanel(ScrolledPanel):
    def __init__(self, parent, frame):
        ScrolledPanel.__init__(self, parent, -1)
        self.frame = frame
        self.parent = parent

        self.SetupScrolling(scroll_y=True, scroll_x=True)

        ## draw event selection tools
        # dropdown for plot selection
        self.WXCB_plot = wx.ComboBox(self,
                                     style=wx.CB_DROPDOWN|wx.CB_READONLY,
                                     size=(250,-1))
        # spin control for event selection
        self.WXSP_plot = wx.SpinCtrl(self, min=1, max=10000000)
        
        ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        ctrlsizer.Add(wx.StaticText(self, label=_("Event:")),0, wx.ALIGN_CENTER)
        ctrlsizer.Add(self.WXCB_plot)
        ctrlsizer.Add(self.WXSP_plot)

        # Bindings
        self.Bind(wx.EVT_COMBOBOX, self.OnShowEvent, self.WXCB_plot)
        self.Bind(wx.EVT_SPINCTRL, self.OnShowEvent, self.WXSP_plot)
        
        ## Image panel with chaco don't work. I get a segmentation fault
        ## with Ubuntu 14.04
        ##
        ## See the bug at launchpad
        ## https://bugs.launchpad.net/ubuntu/+source/python-chaco/+bug/1145575
        #self.plot_window = ea.Window(self)
        #self.vbox = wx.BoxSizer(wx.VERTICAL)
        #self.vbox.Add(self.plot_window.control, 1, wx.EXPAND)
        #self.SetSizer(self.vbox)
        #self.vbox.Fit(self)
        #self.pd = ca.ArrayPlotData()
        #x = np.arange(100).reshape(10,10)
        #a = ca.ImageData()
        #a.set_data(x)
        #self.pd.set_data("cellimg", a)
        #implot = ca.Plot(self.pd)
        #implot.img_plot("cellimg")
        #container = ca.GridPlotContainer(
        #                              shape = (1,1),
        #                              spacing = (0,0),
        #                              padding = (0,0,0,0),
        #                              valign = 'top',
        #                              bgcolor = 'white',
        #                              fill_padding = True,
        #                              use_backbuffer = True)
        #container.add(implot)
        # CAUSE SEGMENTATION FAULT
        #self.plot_window.component = container
        #self.plot_window.redraw()

        # Draw image with wxPython instead
        self.startSizeX = 250
        self.startSizeY = 77
        self.img = wx.EmptyImage(self.startSizeX, self.startSizeY)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, 
                                         wx.BitmapFromImage(self.img))
        #self.mainSizer = wx.BoxSizer(wx.VERTICAL|wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.mainSizer.Add(self.imageCtrl, 1, wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.SetSizer(self.mainSizer)
        #self.mainSizer.Fit(self)
        self.PlotImage()

        ## draw manual filtering options
        self.WXChB_exclude = wx.CheckBox(self, label=_("Exclude event"))
        exclsizer = wx.BoxSizer(wx.HORIZONTAL)
        exclsizer.Add(self.WXChB_exclude, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_CHECKBOX, self.OnChBoxExclude, self.WXChB_exclude)

        # Update Plot button
        updbutton = wx.Button(self, label=_("Update plot"))
        self.Bind(wx.EVT_BUTTON, self.OnUpdatePlot, updbutton)

        #exclsizer.AddSpacer(self.imageCtrl.GetSize()[0]-updbutton.GetSize()[0]-self.WXChB_exclude.GetSize()[0])        
        exclsizer.Add(updbutton, 0, wx.ALIGN_RIGHT)
        
        ## Add traces plot
        # TODO:
        # - write method in dclab that gets all traces across file formats
        x = np.linspace(-np.pi, np.pi, 50)
        y = np.cos(x)+1
        plotkwargs = {}
        for key in dclab.rtdc_dataset.fmt_tdms.naming.tr_data:
            plotkwargs[key[1]] = y
        
        self.trace_data = ca.ArrayPlotData(x=x, **plotkwargs)

        self.trace_plot = ca.Plot(self.trace_data,
                                  padding=0,
                                  spacing=0)

        for key in list(plotkwargs.keys()):
            if key.count("raw"):
                color = "gray"
            elif key == "FL1med":
                color = "green"
            elif key == "FL2med":
                color = "orange"
            elif key == "FL3med":
                color = "red"
            self.trace_plot.plot(("x", key), type="line", color=color)

        container = ca.HPlotContainer(spacing=70,
                                      padding=50,
                                      bgcolor=self.GetBackgroundColour(),
                                      fill_padding=True,)#)
        container.add(self.trace_plot)
        
        self.plot_window = Window(self, component=container)

        sizer = wx.GridBagSizer(5,5)
        sizer.Add(ctrlsizer, (0,0))
        sizer.Add(self.imageCtrl, (1,0))
        sizer.Add(exclsizer, (2,0))
        self.plot_window.control.SetMinSize((300, 300))
        sizer.Add(self.plot_window.control, (3,0), span=(2,2), flag=wx.EXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.sizer = sizer


    def OnChBoxExclude(self, e=None):
        """ If the exclude-check box is triggered, change the
        corresponding value in the measurement."""
        mm_id = self.WXCB_plot.GetSelection()
        evt_id = self.WXSP_plot.GetValue() - 1
        mm = self.analysis.measurements[mm_id]
        mm.filter.manual[evt_id] = not self.WXChB_exclude.GetValue()


    def OnUpdatePlot(self, e=None):
        """ Update the entire plot with filters
        """
        self.frame.PanelTop.OnChangeFilter()
        
    
    def OnShowEvent(self, e=None):
        """ Called when self.WXCB_plot and self.WXSP_plot are selected """
        mm_id = self.WXCB_plot.GetSelection()
        evt_id = self.WXSP_plot.GetValue() - 1

        if mm_id == -1:
            return
        
        if evt_id == -1:
            evt_id = 0

        self.ShowEvent(mm_id, evt_id)


    def ShowEvent(self, mm_id, evt_id):
        """
        Parameters
        ----------
        
        mm_id : int
            measurement identifier (index in self.analysis.measurements)
        evt_id : int
            frame identifier, starts at 0
        
        """
        wx.BeginBusyCursor()
        self.UpdateSelections(mm_id=mm_id, evt_id=evt_id)
        mm = self.analysis.measurements[mm_id]

        if "image" in mm:
            # Get the RGB cell image
            try:
                cellimg = mm["image"][evt_id]
            except OSError:
                cellimg = mm["image"].dummy
            # Only load contour data if there is an image file.
            # We don't know how big the images should be so we
            # might run into trouble displaying random contours.
            if "contour" in mm:
                r = cellimg[:,:,0]
                b = cellimg[:,:,1]
                g = cellimg[:,:,2]
                try:
                    cont = mm["contour"][evt_id]
                except IndexError:
                    pass
                else:
                    r[cont[:,1], cont[:,0]] = 255
                    b[cont[:,1], cont[:,0]] = 0
                    g[cont[:,1], cont[:,0]] = 0
            self.PlotImage(cellimg)
        else:
            # Reset plot if there is not image data
            self.PlotImage(None)

        # Update exclude check-box
        self.WXChB_exclude.SetValue(not mm.filter.manual[evt_id])

        # Set max value for spin control
        max_evt = len(self.analysis.measurements[mm_id])
        self.WXSP_plot.SetRange(1, max_evt)

        # Plot traces
        if "trace" in mm:
            self.plot_window.control.Show(True)
            empty_traces = []
            for ch in mm["trace"]:
                data = mm["trace"][ch][evt_id]
                if data.size == 0:
                    empty_traces.append(ch)
                else:
                    # Set y values for present traces
                    self.trace_data.set_data(ch, data)
                    dshape = data.shape
            else:
                dshape=(10,1)
            # Set x-values for all plots
            self.trace_data.set_data("x", np.arange(dshape[0]))
            # Set other trace data to zero if event does not have it
            zerodata = np.zeros(dshape[0])
            for ech in empty_traces:
                self.trace_data.set_data(ech, zerodata)

        else:
            self.plot_window.control.Show(False)
        self.Layout()
        self.GetParent().Layout()
        wx.EndBusyCursor()
       

    def PlotImage(self, image=None):
        def pil_to_wx_bmp(image):
            width, height = image.size
            mybuffer = image.convert('RGB').tobytes()
            bitmap = wx.BitmapFromBuffer(width, height, mybuffer)
            return bitmap
        
        def pil_to_wx_img(image):
            width, height = image.size
            mybuffer = image.convert('RGB').tobytes()
            bitmap = wx.ImageFromBuffer(width, height, mybuffer)
            return bitmap

        if image is None:
            x = np.linspace(0, 255, self.startSizeX*self.startSizeY)
            image = np.array(x.reshape(self.startSizeY,self.startSizeX),
                             dtype=np.uint8)
        
        os = image.shape
        newx = os[1] * 2
        newy = os[0] * 2
        image = Image.fromarray(image)
        
        #wxbmp = pil_to_wx_bmp(image)
        wximg = pil_to_wx_img(image)
        
        # Image scaling
        wximg = wximg.Scale(newx, newy)
        self.img.Destroy()
        self.img = wx.BitmapFromImage(wximg)
        self.imageCtrl.SetBitmap(self.img)
        # Redraw the panel to prevent artifact images on Windows
        #self.Layout()


    def UpdateAnalysis(self, analysis):
        """ Update the choices of the dopdown list with a new analysis """
        self.analysis = analysis
        self.UpdateSelections()


    def UpdateSelections(self, mm_id=None, evt_id=None):
        # Determine plot titles and set selection
        sel = self.WXCB_plot.GetSelection()
        choices = [ m.title for m in self.analysis.measurements ]
        self.WXCB_plot.SetItems(choices)
        
        if mm_id is not None:
            self.WXCB_plot.SetSelection(mm_id)
        elif sel != -1:
            self.WXCB_plot.SetSelection(sel)
        else:
            self.WXCB_plot.SetValue("--")

        if evt_id is not None:
            # Sanity check:
            mm = self.analysis.measurements[mm_id]
            self.WXSP_plot.SetValue(mm["index"][evt_id])
