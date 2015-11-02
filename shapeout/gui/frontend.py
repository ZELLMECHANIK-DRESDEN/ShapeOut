#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - wx frontend components

"""
from __future__ import division, print_function

import chaco
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
import cv2

import numpy as np
import os
import platform
from PIL import Image
import sys
import tempfile
import traceback
import warnings
import wx
from wx.lib.scrolledpanel import ScrolledPanel

import zipfile

from ..configuration import ConfigurationFile
from controls import ControlPanel
from explorer import ExplorerPanel
import gaugeframe
from .. import tlabwrap
import update
import plot

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
        minsize = (900, 700)
        gaugeframe.GaugeFrame.__init__(self, None, -1,
                title = _("%(progname)s - version %(version)s") % {
                        "progname": u"ᶻᵐShapeOut", "version": version},
                size = size)
        self.SetMinSize(minsize)
        
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
            
        self.spright.SetMinimumPaneSize(sy)
        
        # Splitter Window for control panel and cell view
        scrolltop = ScrolledPanel(self.spright, -1)

        # Controls
        self.PanelTop = ControlPanel(scrolltop, self)
        
        # Cell Images
        self.PanelImage = ImagePanel(scrolltop)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.PanelTop, 2, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self.PanelImage, 1, wx.ALL|wx.EXPAND, 5)
        scrolltop.SetSizer(sizer)
        scrolltop.Layout()
        
        # Main Plots
        self.PlotArea = plot.PlotPanel(self.spright, self)
        #self.PlotArea = plot.MainPlotArea(self.spright, self)

        self.spright.SplitHorizontally(scrolltop, self.PlotArea, sy)
        
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
        e2pdf = exportMenu.Append(wx.ID_ANY, _('&Plot (*.pdf)'), 
                       _('Export the plot as a portable document file'))
        self.Bind(wx.EVT_MENU, self.OnMenuExportPDF, e2pdf)
        e2stat = exportMenu.Append(wx.ID_ANY, _('&Statistics (*.tsv)'), 
                       _('Export the information in the statistics tab'))
        self.Bind(wx.EVT_MENU, self.OnMenuExportStatistics, e2stat)
        
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
        info.AddDeveloper(u'Maik Herbig')
        info.AddDeveloper(u'Philipp Rosendahl')
        info.AddDocWriter(u'Paul Müller')
        wx.AboutBox(info)

    
    def OnHelpSoftware(self, e=None):
        # Show About Information
        from dclab import __version__ as dcversion
        from scipy import __version__ as spversion
        from pyper import __version__ as pyperversion
        from .. import _version as so_version
        from ..util import cran
        r_version = cran.get_R_version()
        
        if hasattr(so_version, "repo_tag"):
            version = so_version.repo_tag  # @UndefinedVariable
        else:
            version = so_version.version

        text = "ShapeOut "+version+\
               "\n\nPython "+sys.version+\
               "\n\nModules:"+\
               "\n - chaco "+chaco.__version__+\
               "\n - dclab "+dcversion+\
               "\n - NumPy "+np.__version__+\
               "\n - OpenCV "+cv2.__version__+\
               "\n - pyper "+pyperversion+\
               "\n - SciPy "+spversion+\
               "\n - wxPython "+wx.__version__

        if hasattr(sys, 'frozen'):
            pyinst = "\n\n"
            pyinst += _("This executable has been created using PyInstaller.")
            text += pyinst
            if 'Anaconda' in sys.version or "Continuum Analytics" in sys.version:
                conda = "\n\nPowered by Anaconda"
                text += conda
        
        mtext = "\n\n"
        mtext += "Other software:\n"
        mtext += "\n".join([ "  "+r for r in r_version.split("\n")])
        text += mtext
        
        wx.MessageBox(text, 'Software', wx.OK|wx.ICON_INFORMATION)


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
                            self.config.GetWorkingDirectory("PDF"), "",
                            "PDF file (*.pdf)|*.pdf",
                            wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not path.endswith(".pdf"):
                path += ".pdf"
            self.config.SetWorkingDirectory(os.path.dirname(path), "PDF")
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

    def OnMenuExportStatistics(self, e=None):
        """ Saves statistics results from tab to text file
        
        """
        # Get data
        head, data = self.analysis.GetStatisticsBasic()
        exp = list()
        # Format data
        exp.append("#"+"\t".join(head))
        for subd in data:
            subdnew = list()
            for d in subd:
                if isinstance(d, (str, unicode)):
                    subdnew.append(d.replace("\t", " "))
                else:
                    subdnew.append("{:.5e}".format(d))
            exp.append("\t".join(subdnew))
        for i in range(len(exp)):
            exp[i] += "\n\r"
        # File dialog
        
        dlg = wx.FileDialog(self, "Choose file to save",
                self.config.GetWorkingDirectory("TSV"),
                "", "Tab separated file (*.tsv)|*.tsv;*.TSV",
                wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        # user cannot do anything until he clicks "OK"
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path.lower().endswith(".tsv") is not True:
                path = path+".tsv"
            self.config.SetWorkingDirectory(os.path.dirname(path), "TSV")
            with open(path, 'w') as fd:
                fd.writelines(exp)


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
        self.img = wx.EmptyImage(self.startSizeX, self.startSizeY)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, 
                                         wx.BitmapFromImage(self.img))
        #self.mainSizer = wx.BoxSizer(wx.VERTICAL|wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.mainSizer.Add(self.imageCtrl, 1, wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.SetSizer(self.mainSizer)
        #self.mainSizer.Fit(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.imageCtrl, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)

        self.ShowImage()


    def ShowImage(self, image=None):
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
       

########################################################################



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


