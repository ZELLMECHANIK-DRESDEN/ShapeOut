#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - wx frontend components

"""
from __future__ import division, print_function



import chaco
import chaco.api as ca
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
import cv2  # @UnresolvedImport
from distutils.version import LooseVersion
import enable.api as ea

import numpy as np
import os
import platform
from PIL import Image
import requests
import simplejson
import sys
import tempfile
import traceback
import warnings
import wx
from wx.lib.scrolledpanel import ScrolledPanel

import zipfile

from configuration import ConfigurationFile
from controls import ControlPanel
from explorer import ExplorerPanel
import gaugeframe
import tlabwrap
import update


########################################################################
class ExceptionDialog(wx.MessageDialog):
    """"""
    def __init__(self, msg):
        """Constructor"""
        wx.MessageDialog.__init__(self, None, msg, _("Error"),
                                          wx.OK|wx.ICON_ERROR)   


########################################################################
class Frame(gaugeframe.GaugeFrame):
    """"""
    def __init__(self, version, sessionfile=None):
        """Constructor"""
        self.config = ConfigurationFile()
        self.version = version
        #size = (1300,900)
        size = (1200,700)
        gaugeframe.GaugeFrame.__init__(self, None, -1,
                title = _("%(progname)s - version %(version)s") % {
                        "progname": u"ᶻᵐShapeOut", "version": version},
                size = size)
        self.SetMinSize(size)
        
        sys.excepthook = MyExceptionHook

        ## Menus, Toolbar
        self.InitUI()

        self.sp = wx.SplitterWindow(self, style=wx.SP_3DSASH)
        # This is necessary to prevent "Unsplit" of the SplitterWindow:
        self.sp.SetMinimumPaneSize(100)
        
        self.spright = wx.SplitterWindow(self.sp, style=wx.SP_3DSASH)
        if platform.system() == "Linux":
            sy = 280
        else:
            sy = 230
            
        st = sy
        
        self.spright.SetMinimumPaneSize(sy)
        
        # Splitter Window for control panel and cell view
        self.sptop = wx.SplitterWindow(self.spright, style=wx.SP_3DSASH)
        self.sptop.SetMinimumPaneSize(300)
        
        # Controls
        self.PanelTop = ControlPanel(self.sptop, self)
        
        # Cell Images
        self.PanelImage = ImagePanel(self.sptop)
        
        # Main Plots
        self.PlotArea = PlotArea(self.spright, self)
        
        self.sptop.SplitVertically(self.PanelTop, self.PanelImage, st)
        self.sptop.SetMinimumPaneSize(1000)
        self.spright.SplitHorizontally(self.sptop, self.PlotArea, sy)
        
        ## left panel (file selection)
        ## We need a splitter window here
        self.PanelLeft = ExplorerPanel(self.sp, self)
        self.PanelLeft.BindAnalyze(self.NewAnalysis)

        self.sp.SplitVertically(self.PanelLeft, self.spright,
                                self.PanelLeft.normal_width)

        # We set this to 100 again after show is complete.
        self.spright.SetMinimumPaneSize(sy)
       
        # fake analysis
        self.NewAnalysis([tlabwrap.Fake_RTDC_DataSet(tlabwrap.cfg)])
       
        ## Go
        self.Centre()
        self.Show()
        self.Maximize()
        
        self.spright.SetMinimumPaneSize(100)
        #self.sptop.SetMinimumPaneSize(st)
        
        if sessionfile is not None:
            self.OnMenuLoad(sessionfile=sessionfile)
            
        update.Update(self)

    def InitUI(self):
        """Menus, Toolbar, Statusbar"""
        
        ## Menubar
        self.menubar = wx.MenuBar()
        
        ## File menu
        fileMenu = wx.Menu()
        self.menubar.Append(fileMenu, _('&File'))
        # data
        fpath = fileMenu.Append(wx.ID_REPLACE, _('Find Measurements'), 
                                _('Select .tdms file location'))
        self.Bind(wx.EVT_MENU, self.OnMenuSearchPath, fpath)
        fpathadd = fileMenu.Append(wx.ID_FIND, _('Add Measurements'), 
                                _('Select .tdms file location'))
        self.Bind(wx.EVT_MENU, self.OnMenuSearchPathAdd, fpathadd)
        # clear measurements
        fpathclear = fileMenu.Append(wx.ID_CLEAR, _('Clear Measurements'), 
                             _('Clear unchecked items in project list'))
        self.Bind(wx.EVT_MENU, self.OnMenuClearMeasurements, fpathclear)
        fileMenu.AppendSeparator()
        # save
        fsave = fileMenu.Append(wx.ID_SAVEAS, _('Save Session'), 
                                _('Select .zmso file'))
        self.Bind(wx.EVT_MENU, self.OnMenuSaveSimple, fsave)
        # load
        fload = fileMenu.Append(wx.ID_OPEN, _('Open Session'), 
                                _('Select .zmso file'))
        self.Bind(wx.EVT_MENU, self.OnMenuLoad, fload)
        fileMenu.AppendSeparator()
        # quit
        fquit = fileMenu.Append(wx.ID_EXIT, _('Quit'), 
                                _('Quit ShapeOut'))
        self.Bind(wx.EVT_MENU, self.OnMenuQuit, fquit)
        
        ## Export menu
        exportMenu = wx.Menu()
        self.menubar.Append(exportMenu, _('&Export'))
        e2pdf = exportMenu.Append(wx.ID_ANY, _('Create PDF file'), 
                       _('Export the plot as a portable document file'))
        self.Bind(wx.EVT_MENU, self.OnMenuExportPDF, e2pdf)
        
        self.SetMenuBar(self.menubar)

        ## Help menu
        helpmenu = wx.Menu()
        self.menubar.Append(helpmenu, _('&Help'))
        menuSoftw = helpmenu.Append(wx.ID_ANY, _("&Software"),
                                    _("Information about the software used"))
        self.Bind(wx.EVT_MENU, self.OnHelpSoftware, menuSoftw)
        menuAbout = helpmenu.Append(wx.ID_ABOUT, _("&About"),
                                    _("Information about this program"))
        self.Bind(wx.EVT_MENU, self.OnHelpAbout, menuAbout)
        
        ## Toolbar
        self.toolbar = self.CreateToolBar()
        self.toolbar.AddLabelTool(wx.ID_REPLACE, _('Load Measurements'),
                           bitmap=wx.ArtProvider.GetBitmap(wx.ART_FIND_AND_REPLACE))
        self.toolbar.AddLabelTool(wx.ID_FIND, _('Add Measurements'),
                           bitmap=wx.ArtProvider.GetBitmap(wx.ART_FIND))
        self.toolbar.AddLabelTool(wx.ID_SAVEAS, _('Save Session'),
                           bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))
        self.toolbar.AddLabelTool(wx.ID_OPEN, _('Open Session'),
                           bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        self.toolbar.AddSeparator()
        try:
            # This only works with wxPython3
            self.toolbar.AddStretchableSpace()
        except:
            pass
        self.toolbar.AddLabelTool(wx.ID_EXIT, _('Quit'),
                           bitmap=wx.ArtProvider.GetBitmap(wx.ART_QUIT))
        self.toolbar.Realize() 

        #self.background_color = self.statusbar.GetBackgroundColour()
        #self.statusbar.SetBackgroundColour(self.background_color)
        #self.statusbar.SetBackgroundColour('RED')
        #self.statusbar.SetBackgroundColour('#E0E2EB')
        #self.statusbar.Refresh()
        
        self.Bind(wx.EVT_CLOSE, self.OnMenuQuit)

    def NewAnalysis(self, data):
        """ Create new analysis object and show data """
        wx.BeginBusyCursor()
        anal = tlabwrap.Analysis(data)
        # Get Plotting and Filtering parameters from previous analysis
        if hasattr(self, "analysis"):
            fpar = self.analysis.GetParameters("Filtering")
            ppar = self.analysis.GetParameters("Plotting")
            newcfg = {"Filtering" : fpar,
                      "Plotting" : ppar  }
            # set colors if more than one:
            anal.SetParameters(newcfg)
            # reset contour accuracies
            anal.SetContourAccuracies()
            # set contour colors
            anal.SetContourColors()
            # Automatically reset colors
            #print(anal.measurements[0].Configuration["Plotting"]["Contour Color"])

            # remember contour colors
            colors = self.analysis.GetContourColors()
            anal.SetContourColors(colors)
        self.analysis = anal
        self.PanelTop.NewAnalysis(anal)
        self.PlotArea.Plot(anal)
        wx.EndBusyCursor()

    def OnHelpAbout(self, e=None):
        description =  ("ShapeOut is a data evaluation tool"+
            "\nfor real-time deformability cytometry (RT-DC)."+
            "\nShapeOut is written in Python.")
        licence = """ShapeOut is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published 
by the Free Software Foundation, either version 2 of the License, 
or (at your option) any later version.

ShapeOut is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License 
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
        info = wx.AboutDialogInfo()
        #info.SetIcon(wx.Icon('hunter.png', wx.BITMAP_TYPE_PNG))
        info.SetName('ShapeOut')
        info.SetVersion(self.version)
        info.SetDescription(description)
        info.SetCopyright(u'(C) 2015 Paul Müller')
        info.SetWebSite(u"http://www.zellmechanik.com/")
        info.SetLicence(licence)
        #info.SetIcon(misc.getMainIcon(pxlength=64))
        info.AddDeveloper(u'Paul Müller')
        info.AddDocWriter(u'Paul Müller')
        wx.AboutBox(info)

    
    def OnHelpSoftware(self, e=None):
        # Show About Information
        import dclab
        import scipy
        text = "Python "+sys.version+\
               "\n\nModules:"+\
               "\n - chaco "+chaco.__version__+\
               "\n - dclab "+dclab.__version__+\
               "\n - NumPy "+np.__version__+\
               "\n - OpenCV "+cv2.__version__+\
               "\n - SciPy "+scipy.__version__+\
               "\n - wxPython "+wx.__version__

        if hasattr(sys, 'frozen'):
            pyinst = "\n\n"
            pyinst += _("This executable has been created using PyInstaller.")
            text += pyinst
            if 'Anaconda' in sys.version or "Continuum Analytics" in sys.version:
                conda = "\n\nPowered by Anaconda"
                text += conda
        wx.MessageBox(text, 'Software', wx.OK | wx.ICON_INFORMATION)


    def OnMenuClearMeasurements(self, e=None):
        tree = self.PanelLeft.htreectrl
        r = tree.GetRootItem()
        dellist = []
        # iterate through all measurements
        for c in r.GetChildren():
            for ch in c.GetChildren():
                # keep those:
                # - bold means it was analyzed
                # - checked means user wants to analyze next
                if not ch.IsChecked() and not ch.IsBold():
                    dellist.append(ch)
        for ch in dellist:
            tree.Delete(ch)
        dellist = []
        # find empty parents
        for c in r.GetChildren():
            if len(c.GetChildren()) == 0:
                dellist.append(c)
        for ch in dellist:
            tree.Delete(ch)

    def OnMenuExportPDF(self, e=None):
        """ Saves plot container as PDF
        
        Uses heuristic methods to resize
        - the plot
        - the scatter plot markers
        and then changes everything back
        """
        dlg = wx.FileDialog(self, "Export plot as PDF", 
                            self.config.GetWorkingDirectory(), "",
                            "PDF file (*.pdf)|*.pdf",
                            wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not path.endswith(".pdf"):
                path += ".pdf"
            container = self.PlotArea.container
            
            #old_height = container.height
            #old_width = container.width
            
            
            
            #a4_factor = 297/210
            ## Segmentation-faults:
            #from chaco.api import PlotGraphicsContext
            #gc = PlotGraphicsContext((int(container.outer_width), int(container.outer_height)))
            #container.draw(gc, mode="normal")
            #gc.save(path)

            #container.auto_size=True
            #container.auto_center=True
            
            # get inner_boundary
            (bx, by) = container.outer_bounds
            
            #(x, y) = (bx, by) = container.outer_bounds
            #x2 = 0,
            #y2 = 0
            #for c in container.components:
            #    x = min(c.x, x)
            #    y = min(c.y, y)
            #    x2 = max(c.x2, x2)
            #    y2 = max(c.y2, y2)
            #container.set_outer_bounds(0, (x2-x))
            #container.set_outer_bounds(1, (y2-y))

            # Correction factor 0.9 wih size of plots yields
            # approximately the right size for all kinds of container
            # shapes.
            container.set_outer_bounds(0, (300)*container.shape[1]**.9)
            container.set_outer_bounds(1, (300)*container.shape[0]**.9)
            
            for c in container.components:
                for comp in c.components:
                    if isinstance(comp, 
                  chaco.colormapped_scatterplot.ColormappedScatterPlot):
                        comp.marker_size /= 2
            
            
            dest_box = (.01, .01, -.01, -.01)
            try:
                gc = PdfPlotGraphicsContext(filename=path,
                                    dest_box = dest_box,
                                    pagesize="landscape_A4")
            except KeyError:
                warnings.warn("'landscape_A4' not defined for pdf "+\
                              "export. Please update `chaco`.")
                gc = PdfPlotGraphicsContext(filename=path,
                                    dest_box = dest_box,
                                    pagesize="A4")
            # draw the plot
            gc.render_component(container, halign="center",
                                valign="top")
            #Start a new page for subsequent draw commands.
            gc.save()
            container.set_outer_bounds(0, bx)
            container.set_outer_bounds(1, by)

            for c in container.components:
                for comp in c.components:
                    if isinstance(comp, 
                  chaco.colormapped_scatterplot.ColormappedScatterPlot):
                        comp.marker_size *= 2

            #container.height = old_height
            #container.width = old_width
            #container.auto_size = True
            #container.auto_size = False

    ## TODO:
    ## Put this into a differnt function in PlotArea
    ## -> call it after each plot
            ## Solves font Error after saving PDF:
            # /usr/lib/python2.7/dist-packages/kiva/fonttools/font_manag
            # er.py:1303: UserWarning: findfont: Could not match 
            # (['Bitstream Vera Sans'], 'normal', None, 'normal', 500, 
            # 12.0). Returning /usr/share/fonts/truetype/lato/
            # Lato-Hairline.ttf UserWarning)
            for aplot in container.plot_components:
                for item in aplot.overlays:
                    if isinstance(item, chaco.plot_label.PlotLabel):
                        item.font = "modern 12"
                    elif isinstance(item, chaco.legend.Legend):
                        item.font = "modern 10"
                    elif isinstance(item, chaco.axis.PlotAxis):
                        item.title_font = "modern 12"
                        item.tick_label_font = "modern 10"
                    elif isinstance(item, chaco.data_label.DataLabel):
                        item.font = "modern 9"
                    else:
                        warnings.warn("Not resetting plot fonts for"+\
                                      "plot component class {}.".format(
                                      item.__class__))


    def OnMenuLoad(self, e=None, sessionfile=None):
        """ Load entire analysis """
        if sessionfile is None:
            dlg = wx.FileDialog(self, "Open session file",
                    self.config.GetWorkingDirectory(name="Session"), "",
                            "ShapeOut session (*.zmso)|*.zmso", wx.FD_OPEN)
            
            if dlg.ShowModal() == wx.ID_OK:
                self.config.SetWorkingDirectory(dlg.GetDirectory(),
                                                name="Session")
                fname = dlg.GetPath()
                dlg.Destroy()
            else:
                self.config.SetWorkingDirectory(dlg.GetDirectory(),
                                                name="Session")
                dlg.Destroy()
                return # nothing more to do here
        else:
            fname = sessionfile 
        
        dirname = os.path.dirname(fname)
        self.config.SetWorkingDirectory(dirname)
        Arc = zipfile.ZipFile(fname, mode='r')
        tempdir = tempfile.mkdtemp()
        Arc.extractall(tempdir)
        Arc.close()
        
        indexfile = os.path.join(tempdir, "index.txt")

        delist = [self, self.PanelTop, self.PlotArea]
        for item in delist:
            if hasattr(item, "analysis"):
                del item.analysis

        self.NewAnalysis(indexfile)

        directories = list()
        for mm in self.analysis.measurements:
            if os.path.exists(mm.fdir):
                directories.append(mm.fdir)
        
        # TODO: mark loaded directories as bold
        bolddirs = self.analysis.GetTDMSFilenames()

        self.OnMenuSearchPathAdd(add=False, path=directories,
                                 marked=bolddirs)
        

    def OnMenuSearchPath(self, e=None):
        """ Set path of working directory
        
        Display Dialog to select folder and update Content of PanelLeft.
        This calls `PanelLeft.SetProjectTree`.
        """
        dlg = wx.DirDialog(self, _("Please select a directory"),
               defaultPath=self.config.GetWorkingDirectory(name="Main"))
        answer = dlg.ShowModal()
        if answer == wx.ID_OK:
            path = dlg.GetPath()
            self.config.SetWorkingDirectory(path, name="Main")
            dlg.Destroy()
            self.GaugeIndefiniteStart(
                                func=tlabwrap.GetTDMSTreeGUI,
                                func_args=(path,),
                                post_call=self.PanelLeft.SetProjectTree,
                                msg=_("Searching for .tdms files")
                                     )


    def OnMenuSearchPathAdd(self, e=None, add=True, path=None,
                            marked=[]):
        """ Convenience wrapper around OnMenuSearchPath"""
        if path is None:
            dlg = wx.DirDialog(self, _("Please select a directory"),
                          defaultPath=self.config.GetWorkingDirectory())
            answer = dlg.ShowModal()
            path = dlg.GetPath()
            self.config.SetWorkingDirectory(path, name="Main")
            dlg.Destroy()
            if answer != wx.ID_OK:
                return
            
        self.GaugeIndefiniteStart(
                        func=tlabwrap.GetTDMSTreeGUI,
                        func_args=(path,),
                        post_call=self.PanelLeft.SetProjectTree,
                        post_call_kwargs = {"add":add, "marked":marked},
                        msg=_("Searching for .tdms files")
                                 )

    def OnMenuQuit(self, e=None):
        if hasattr(self, "analysis") and self.analysis is not None:
            # Ask to save the session
            dial = wx.MessageDialog(self, 
                'Do you want to save the current Session?', 
                'Save Session?', 
                 wx.ICON_QUESTION | wx.CANCEL | wx.YES_NO | wx.NO_DEFAULT )
            result = dial.ShowModal()
            dial.Destroy()
            if result == wx.ID_CANCEL:
                return # abort
            elif result == wx.ID_YES:
                filename = self.OnMenuSaveSimple()
                if filename is None:
                    # User did not save session - abort
                    return
        #self.Close()
        #self.Destroy()
        #sys.exit()
        # Force Exit without cleanup
        os._exit(0)


    def OnMenuSaveSimple(self, e=None):
        """ Save configuration without measurement data """
        dlg = wx.FileDialog(self, "Save ShapeOut session", 
                    self.config.GetWorkingDirectory(name="Session"), "",
                    "ShapeOut session (*.zmso)|*.zmso",
                    wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            # Save everything
            path = dlg.GetPath()
            if not path.endswith(".zmso"):
                path += ".zmso"
            dirname = os.path.dirname(path)
            self.config.SetWorkingDirectory(dirname, name="Session")
            # Begin saving
            returnWD = os.getcwd()
            tempdir = tempfile.mkdtemp()
            os.chdir(tempdir)
            Arc = zipfile.ZipFile(path, mode='w')
            ## Dump data into directory
            self.analysis.DumpData(tempdir)
            for root, _dirs, files in os.walk(tempdir):
                for f in files:
                    fw = os.path.join(root,f)
                    Arc.write(os.path.relpath(fw,tempdir))
                    os.remove(fw)
            Arc.close()
            os.chdir(returnWD)
            return path
        else:
            dirname = dlg.GetDirectory()
            self.config.SetWorkingDirectory(dirname, name="Session")
            dlg.Destroy()


    def OnMenuSaveFull(self, e=None):
        """ Save configuration including measurement data """
        pass


class ImagePanel(ScrolledPanel):
    def __init__(self, parent):
        ScrolledPanel.__init__(self, parent, -1)
        self.parent = parent
        
        self.SetupScrolling(scroll_y=True, scroll_x=True)
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
        self.startSizeY = 80
        img = wx.EmptyImage(self.startSizeX, self.startSizeY)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, 
                                         wx.BitmapFromImage(img))
        #self.mainSizer = wx.BoxSizer(wx.VERTICAL|wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.mainSizer.Add(self.imageCtrl, 1, wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.SetSizer(self.mainSizer)
        #self.mainSizer.Fit(self)

        self.ShowImage()


    def ShowImage(self, image=None):
        def pil_to_wx_bmp(image):
            width, height = image.size
            mybuffer = image.convert('RGB').tostring()
            bitmap = wx.BitmapFromBuffer(width, height, mybuffer)
            return bitmap
        
        def pil_to_wx_img(image):
            width, height = image.size
            mybuffer = image.convert('RGB').tostring()
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

        self.imageCtrl.SetBitmap(wx.BitmapFromImage(wximg))
        
        self.SetClientSize((newx, newy))
        self.SetMaxSize((newx, newy))
        self.SetVirtualSize((newx, newy))
        self.parent.SetSashPosition(self.parent.GetSashPosition())
       

########################################################################
class PlotArea(wx.Panel):
    def __init__(self, parent, frame):
        self.frame = frame
        wx.Panel.__init__(self, parent, -1)

        self.plot_window = ea.Window(self)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.plot_window.control, 1, wx.EXPAND)
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)


    def Plot(self, anal=None):
        self._lastplot = -1
        self._lastselect = -1
        self._lasthover = -1
        
        if anal is not None:
            self.analysis = anal
        
        anal = self.analysis
        
        xax, yax = anal.GetPlotAxes()
        
        rows, cols, lcc, lll = anal.GetPlotGeometry()
        
        numplots = rows * cols

        container = ca.GridPlotContainer(
                                      shape = (rows,cols),
                                      spacing = (0,0),
                                      padding = (0,0,0,0),
                                      valign = 'top',
                                      bgcolor = 'white',
                                      fill_padding = True,
                                      use_backbuffer = True)
                                      

        maxplots = min(len(anal.measurements), numplots)

        self.index_datasources = list()

        # dictionary mapping plot objects to data for scatter plots
        scatter2measure = {}

        c_plot = 0
        legend_plotted = False
        range_joined = list()
        for j in range(rows):
            for i in range(cols):
                #k = i + j*rows
                if (i == cols-1 and j == 0 and lcc == 1):
                    # Contour plot in upper right corner
                    aplot = tlabwrap.CreateContourPlot(anal.measurements,
                                               xax=xax, yax=yax,
                                               levels=[0.5,0.95])
                    range_joined.append(aplot)
                elif (i == cols-1 and j == 1 and lll == 1):
                    # Legend plot below contour plot
                    aplot = tlabwrap.CreateLegendPlot(anal.measurements)
                    legend_plotted = True
                elif c_plot < maxplots:
                    # Scatter Plot
                    aplot = tlabwrap.CreateScatterPlot(anal.measurements[c_plot],
                                               xax=xax, yax=yax)
                    scatter2measure[aplot] = anal.measurements[c_plot]
                    range_joined.append(aplot)
                    c_plot += 1
                    # Retrieve the plot hooked to selection tool
                    my_plot = aplot.plots["my_plot"][0]
                    # Set up the trait handler for the selection
                    id_ds = my_plot.index

                    id_ds.on_trait_change(self.OnMouseScatter,
                                          "metadata_changed")
                    self.index_datasources.append((aplot, id_ds))
                elif (not legend_plotted and lll == 1 and rows == 1) :
                    # Legend plot in next free window
                    aplot = tlabwrap.CreateLegendPlot(anal.measurements)
                    legend_plotted = True
                else:
                    # dummy plot
                    aplot = ca.Plot()
                    aplot.aspect_ratio = 1
                    aplot.range2d.low = (0,0)
                    aplot.range2d.high = (1,1)
                    aplot.y_axis = None
                    aplot.x_axis = None
                    aplot.x_grid = None
                    aplot.y_grid = None
                
                container.add(aplot)

        # connect all plots' panning and zooming
        comp = None
        for comp in range_joined[1:]:
            comp.range2d = container.components[0].range2d
            comp.components[-1].marker_size = container.components[0].components[-1].marker_size
        
        # Connect range with displayed range
        if comp is not None:
            comp.range2d.on_trait_change(self.OnPlotRangeChanged)

        container.padding = 10
        container.padding_left = 30
        container.padding_right = 5

        (bx, by) = container.outer_bounds
        container.set_outer_bounds(0, bx)
        container.set_outer_bounds(1, by)
        self.container = container
        self.scatter2measure = scatter2measure

        self.plot_window.component = container

        self.plot_window.redraw()


    def OnPlotRangeChanged(self, obj, name, new):
        """ Is called by traits on_trait_change for plots
            
        Updates the data in panel top
        """
        ctrls = self.frame.PanelTop.page_plot.GetChildren()
        #samdict = self.analysis.measurements[0].\
        #                               Configuration["Plotting"].copy()
        newfilt = dict()
 
        xax, yax = self.analysis.GetPlotAxes()
 
        # identify controls via their name correspondence in the cfg
        for c in ctrls:
            name = c.GetName()
            if   name == xax+" Min":
                ol0 = float("{:.4e}".format(obj.low[0]))
                newfilt[name] = ol0
                c.SetValue(unicode(ol0))
            elif name == xax+" Max":
                oh0 = float("{:.4e}".format(obj.high[0]))
                newfilt[name] = oh0
                c.SetValue(unicode(oh0))
            elif name == yax+" Min":
                ol1 = float("{:.4e}".format(obj.low[1]))
                newfilt[name] =ol1
                c.SetValue(unicode(ol1))
            elif name == yax+" Max":
                oh1 = float("{:.4e}".format(obj.high[1]))
                newfilt[name] = oh1
                c.SetValue(unicode(oh1))
                

        cfg = { "Plotting" : newfilt }
        self.analysis.SetParameters(cfg)

    def OnMouseScatter(self):
        # TODO:
        # - detect when hover is stuck
        # - display additional information in plot
        
        if not hasattr(self, "_lasthover"):
            self._lasthover = False
        if not hasattr(self, "_lastselect"):
            self._lastselect = False
        if not hasattr(self, "_lastplothover"):
            self._lastplothover = False
        if not hasattr(self, "_lastplotselect"):
            self._lastplotselect = False
        
        thisplothover = None
        thisplotselect = None
        thissel = None
        thishov = None
        for (aplot, id_ds) in self.index_datasources:
            hov = id_ds.metadata.get("hover", [])
            sel = id_ds.metadata.get("selections", [])
            # Get hover data
            if len(hov) > 0:
                thisplothover = aplot
                thishov = hov[0]
                # Get select data
                if len(sel) != 0:
                    thisplotselect = aplot
                    thissel = sel[0]
        
        if thishov is None:        
            for (aplot, id_ds) in self.index_datasources:
                if self._lastplothover is aplot:
                    thisplothover = aplot

        for (aplot, id_ds) in self.index_datasources:
            my_plot = aplot.plots["my_plot"][0]
            # Show or hide overlays:
            if thisplothover is aplot:
                my_plot.overlays[0].visible = True
            else:
                my_plot.overlays[0].visible = False

        action = False

        if thisplotselect is not None:
            if self._lastplotselect is thisplotselect:
                # We are in the same plot
                if self._lastselect != thissel:
                    # We have a different cell
                    action = True
            else:
                # We have a new plot
                action = True


        if action:
            # Get the cell and plot it
            dataset = self.scatter2measure[thisplotselect]
            # these are all cells that were plotted
            plotfilterid = np.where(dataset._plot_filter)[0]
            # this is the plot selection
            plot_sel = plotfilterid[thissel]
            # these are all the filtered cells
            filterid = np.where(dataset._filter)[0]
            actual_sel = filterid[plot_sel]
            
            #vfile = os.path.join(dataset.fdir, dataset.video)
            os.chdir(dataset.fdir)
            video = cv2.VideoCapture(dataset.video)
            totframes = video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
            
            video.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, actual_sel-1)
            
            flag, cellimg = video.read()

            if flag:
                # add contour in red
                if len(cellimg.shape) == 2:
                    # convert grayscale to color
                    cellimg = np.tile(cellimg, [3,1,1]).transpose(1,2,0)
                
                
                r = cellimg[:,:,0]
                b = cellimg[:,:,1]
                g = cellimg[:,:,2]
                
                # only do this if there was a contour file loaded
                if len(dataset.contours) > 0:
                    contours = dataset.contours[dataset.frame[actual_sel]]
                    
                    r[contours[:,1], contours[:,0]] = 255
                    b[contours[:,1], contours[:,0]] = 0
                    g[contours[:,1], contours[:,0]] = 0
                
                self.frame.PanelImage.ShowImage(cellimg)
            
            video.release()
            print("Frame {} / {}".format(actual_sel, totframes))


        if not thisplothover is None:
            self._lastplothover = thisplothover
        if not thisplotselect is None:
            self._lastplotselect = thisplotselect
        self._lasthover = thishov
        self._lastselect = thissel

    def CheckTightLayout(self):
        """ Determine whether a call to tight_layout is necessary and
            (do not) do it.
        """
        if not self.tight_layout:
            self.figure.tight_layout()
            self.tight_layout = True
        #self.figure.tight_layout(pad=0.5, h_pad=0, w_pad=0)



def MyExceptionHook(etype, value, trace):
    """
    Handler for all unhandled exceptions.
 
    :param `etype`: the exception type (`SyntaxError`, `ZeroDivisionError`, etc...);
    :type `etype`: `Exception`
    :param string `value`: the exception error message;
    :param string `trace`: the traceback header, if any (otherwise, it prints the
     standard Python header: ``Traceback (most recent call last)``.
    """
    wx.GetApp().GetTopWindow()
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join(tmp)
 
    dlg = ExceptionDialog(exception)
    dlg.ShowModal()
    dlg.Destroy()     
    wx.EndBusyCursor()


