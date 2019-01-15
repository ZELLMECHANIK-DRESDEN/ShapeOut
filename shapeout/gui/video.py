#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - wx frontend components"""
from __future__ import division, print_function, unicode_literals

import chaco.api as ca
import dclab
from enable.api import Window
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
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
        ctrlsizer.Add(wx.StaticText(self, label="Event:"),0, wx.ALIGN_CENTER)
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
        self.WXChB_exclude = wx.CheckBox(self, label="Exclude event")
        exclsizer = wx.BoxSizer(wx.HORIZONTAL)
        exclsizer.Add(self.WXChB_exclude, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_CHECKBOX, self.OnChBoxExclude, self.WXChB_exclude)

        # Update Plot button
        updbutton = wx.Button(self, label="Update plot")
        self.Bind(wx.EVT_BUTTON, self.OnUpdatePlot, updbutton)

        #exclsizer.AddSpacer(self.imageCtrl.GetSize()[0]-updbutton.GetSize()[0]-self.WXChB_exclude.GetSize()[0])        
        exclsizer.Add(updbutton, 0, wx.ALIGN_RIGHT)
        
        ## Add traces plot
        # set initial values
        x = np.linspace(-np.pi, np.pi, 50)
        y = np.cos(x)+1
        plotkwargs = {}
        for trid in dclab.definitions.FLUOR_TRACES:
            plotkwargs[trid] = y
        
        self.trace_data = ca.ArrayPlotData(x=x, **plotkwargs)

        self.trace_plot = ca.Plot(self.trace_data,
                                  padding=0,
                                  spacing=0)

        for trid in dclab.definitions.FLUOR_TRACES:
            if trid.count("raw"):
                color = "gray"
            elif trid == "fl1_median":
                color = "green"
            elif trid == "fl2_median":
                color = "orange"
            elif trid == "fl3_median":
                color = "red"
            self.trace_plot.plot(("x", trid), type="line", color=color)
        
        # convert wx color to something chaco understands
        bgcolor = list(np.array(self.GetBackgroundColour()) / 255)
        container = ca.HPlotContainer(spacing=70,
                                      padding=50,
                                      bgcolor=bgcolor,
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


    def GetImage(self, contour=True):
        """Returns the currently selected image
        
        Parameters
        ----------
        contour: bool
            Draws the contour (red) ontop of the image, if
            it is available.
        
        Returns
        -------
        image: PIL.Image
            The image of the event.
        """
        # Get dataset ID
        ds_id = self.WXCB_plot.GetSelection()
        # Get the event ID
        evt_id = self.WXSP_plot.GetValue() - 1
        if evt_id == -1:
            evt_id = 0
        # Get dataset
        if hasattr(self, "analysis"):
            ds = self.analysis.measurements[ds_id]
        else:
            assert ds_id == -1

        if (ds_id != -1 and "image" in ds and len(ds["image"]) > evt_id):
            # Get the gray scale cell image
            cellimg = ds["image"][evt_id]
            if np.all(np.isnan(cellimg)):
                # No image data - return white image
                cellimg = 255*np.ones_like(cellimg, dtype=np.uint8)
            # Convert to RGB
            cellimg = cellimg.reshape(cellimg.shape[0], cellimg.shape[1], 1)
            cellimg = np.repeat(cellimg, 3, axis=2)
            # Only load contour data if there is an image column.
            # We don't know how big the images should be so we
            # might run into trouble displaying random contours.
            if (contour and "mask" in ds and len(ds["mask"]) > evt_id):
                mask = ds["mask"][evt_id]
                # compute contour image from mask
                cont = mask ^ binary_erosion(mask)
                # set red contour pixel values in original image
                cellimg[cont, 0] = 255
                cellimg[cont, 1] = 0
                cellimg[cont, 2] = 0
        else:
            x = np.linspace(0, 255, self.startSizeX*self.startSizeY)
            cellimg = np.array(x.reshape(self.startSizeY,self.startSizeX),
                               dtype=np.uint8)
        
        image = Image.fromarray(cellimg)
        return image


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

        mm = self.analysis.measurements[mm_id]
        if evt_id > len(mm):
            evt_id = 0

        # Set max value for spin control
        max_evt = len(self.analysis.measurements[mm_id])
        self.WXSP_plot.SetRange(1, max_evt)

        self.UpdateSelections(mm_id=mm_id, evt_id=evt_id)

        self.PlotImage()

        # Update exclude check-box
        self.WXChB_exclude.SetValue(not mm.filter.manual[evt_id])

        # Plot traces
        if "trace" in mm:
            self.plot_window.control.Show(True)
            empty_traces = []
            # Default shape needed for zero-data
            # (will be overridden by this loop if there
            # is trace data for this event.
            dshape = (10,1)
            for trid in dclab.definitions.FLUOR_TRACES:
                if trid in mm["trace"]:
                    data = mm["trace"][trid][evt_id]
                    # Set y values for present traces
                    self.trace_data.set_data(trid, data)
                    dshape = data.shape
                else:
                    empty_traces.append(trid)

            # Set x-values for all plots
            self.trace_data.set_data("x", np.arange(dshape[0]))
            # Set other trace data to zero if event does not have it
            zerodata = np.zeros(dshape[0])
            for etr in empty_traces:
                self.trace_data.set_data(etr, zerodata)

        else:
            self.plot_window.control.Show(False)
        self.Layout()
        self.GetParent().Layout()
        wx.EndBusyCursor()
       

    def PlotImage(self, image=None):
        if image is None:
            image = self.GetImage()

        width, height = image.size
        mybuffer = image.convert('RGB').tobytes()
        wximg = wx.ImageFromBuffer(width, height, mybuffer)

        # Image scaling
        wximg = wximg.Scale(width*2, height*2)
        self.img.Destroy()
        self.img = wx.BitmapFromImage(wximg)
        self.imageCtrl.SetBitmap(self.img)


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
            if evt_id > len(mm):
                self.WXSP_plot.SetValue(1)
            else:
                self.WXSP_plot.SetValue(mm["index"][evt_id])
