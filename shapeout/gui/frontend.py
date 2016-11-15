#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - wx frontend components

"""
from __future__ import division, print_function

import chaco

import cv2
import numpy as np
import os
import platform
import sys
import traceback
import wx

import dclab

from ..configuration import ConfigurationFile
from ..util import findfile
from .controls import ControlPanel
from .explorer import ExplorerPanel
import gaugeframe
from .. import analysis
from .. import tlabwrap
from . import autosave
from . import update
from . import plot_main
from . import misc
from . import video
from . import export
from . import batch
from . import plot_export
from . import session


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
    def __init__(self, version):
        """Constructor"""
        self.config = ConfigurationFile(findfile("shapeout.cfg"))
        self.version = version
        #size = (1300,900)
        size = (1200,700)
        minsize = (900, 700)
        gaugeframe.GaugeFrame.__init__(self, None, -1,
                title = _("%(progname)s - version %(version)s") % {
                        "progname": "ShapeOut", "version": version},
                size = size)
        self.SetMinSize(minsize)
        
        sys.excepthook = MyExceptionHook

        ## Menus, Toolbar
        self.InitUI()

        self.sp = wx.SplitterWindow(self, style=wx.SP_THIN_SASH)
        # This is necessary to prevent "Unsplit" of the SplitterWindow:
        self.sp.SetMinimumPaneSize(100)
        
        self.spright = wx.SplitterWindow(self.sp, style=wx.SP_THIN_SASH)
        if platform.system() == "Linux":
            sy = 270
        else:
            sy = 230
            
        self.spright.SetMinimumPaneSize(sy)
        
        # Splitter Window for control panel and cell view
        self.sptop = wx.SplitterWindow(self.spright, style=wx.SP_THIN_SASH)
        self.sptop.SetMinimumPaneSize(sy)

        # Controls
        self.PanelTop = ControlPanel(self.sptop, frame=self)
        
        # Cell Images
        self.ImageArea = video.ImagePanel(self.sptop, frame=self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.PanelTop, 2, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self.ImageArea, 1, wx.ALL|wx.EXPAND, 5)
        
        self.sptop.SplitVertically(self.PanelTop, self.ImageArea, sy)
        self.sptop.SetSashGravity(.46)
        
        # Main Plots
        self.PlotArea = plot_main.PlotPanel(self.spright, self)

        self.spright.SplitHorizontally(self.sptop, self.PlotArea, sy)
        
        ## left panel (file selection)
        ## We need a splitter window here
        self.PanelLeft = ExplorerPanel(self.sp, self)
        self.PanelLeft.BindAnalyze(self.NewAnalysis)

        self.sp.SplitVertically(self.PanelLeft, self.spright,
                                self.PanelLeft.normal_width)

        # We set this to 100 again after show is complete.
        self.spright.SetMinimumPaneSize(sy)
       
        # Fake analysis
        ddict = {"Area" : np.arange(10)*30,
                 "Defo" : np.arange(10)*.02}
        rtdc_ds = dclab.RTDC_DataSet(ddict=ddict)
        rtdc_ds.Configuration["Plotting"]["Contour Color"] = "white"
        self.NewAnalysis([rtdc_ds])

        ## Go
        self.Centre()
        self.Show()
        self.Maximize()
        
        self.spright.SetMinimumPaneSize(100)
        self.sptop.SetMinimumPaneSize(100)
        
        # Set window icon
        try:
            self.MainIcon = misc.getMainIcon()
            wx.Frame.SetIcon(self, self.MainIcon)
        except:
            self.MainIcon = None


    def InitRun(self, session_file=None):
        """Performs the first tasks after the publication starts
        
        - start autosaving
        - check for updates
        """
        # Check if we have an autosaved session that we did not delete
        recover = autosave.check_recover(self)
        
        # Load session file if provided
        if session_file is not None and not recover:
            self.OnMenuLoad(session_file=session_file)
            
        # Search for updates
        update.Update(self)

        # Start autosaving
        autosave.autosave_run(self)


    def InitUI(self):
        """Menus, Toolbar, Statusbar"""
        
        ## Menubar
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        
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
        e2dat = exportMenu.Append(wx.ID_ANY, _('All &event data (*.tsv)'), 
                       _('Export the plotted event data as tab-separated values'))
        self.Bind(wx.EVT_MENU, self.OnMenuExportData, e2dat)
        e2pdf = exportMenu.Append(wx.ID_ANY, _('Graphical &plot (*.pdf)'), 
                       _('Export the plot as a portable document file'))
        self.Bind(wx.EVT_MENU, self.OnMenuExportPDF, e2pdf)
        # export PNG disabled:
        # https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut/issues/62
        #e2png = exportMenu.Append(wx.ID_ANY, _('Graphical &plot (*.png)'), 
        #               _('Export the plot as a portable network graphic'))
        #self.Bind(wx.EVT_MENU, self.OnMenuExportPNG, e2png)
        e2stat = exportMenu.Append(wx.ID_ANY, _('Computed &statistics (*.tsv)'), 
                       _('Export the statistics data as tab-separated values'))
        self.Bind(wx.EVT_MENU, self.OnMenuExportStatistics, e2stat)

        ## Batch menu
        batchMenu = wx.Menu()
        self.menubar.Append(batchMenu, _('&Batch'))
        b_filter = batchMenu.Append(wx.ID_ANY, _('&Statistical analysis'), 
                    _('Apply one filter setting to multiple measurements.'))
        self.Bind(wx.EVT_MENU, self.OnMenuBatchFolder, b_filter)
        
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
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT|wx.TB_HORIZONTAL|wx.TB_NODIVIDER)
        iconsize = (36,36)
        self.toolbar.SetToolBitmapSize(iconsize)
        
        names = [['Load Measurements', wx.ID_REPLACE, wx.ART_FIND_AND_REPLACE],
                 ['Add Measurements', wx.ID_FIND, wx.ART_FIND],
                 ['Save Session', wx.ID_SAVEAS, wx.ART_FILE_SAVE_AS],
                 ['Open Session', wx.ID_OPEN, wx.ART_FILE_OPEN],
                ]
        
        def add_icon(name):
            self.toolbar.AddLabelTool(name[1],
                                      _(name[0]),
                                      bitmap=wx.ArtProvider.GetBitmap(
                                                                  name[2],
                                                                  wx.ART_TOOLBAR,
                                                                  iconsize))
        
        def add_image(name, height=-1, width=-1):
            png = wx.Image(findfile(name), wx.BITMAP_TYPE_ANY)
            image = wx.StaticBitmap(self.toolbar, -1, png.ConvertToBitmap(), size=(width,height))
            self.toolbar.AddControl(image)
        
        for name in names:
            add_icon(name)
        
        add_image("transparent_h50.png", width=75, height=iconsize[0])
        add_image("zm_logo_h36.png")        

        try:
            # This only works with wxPython3
            self.toolbar.AddStretchableSpace()
        except:
            pass

        add_image("shapeout_logotype_h36.png")

        try:
            # This only works with wxPython3
            self.toolbar.AddStretchableSpace()
        except:
            pass
        
        add_image("transparent_h50.png", height=iconsize[0])
        add_icon(['Quit', wx.ID_EXIT, wx.ART_QUIT])
        self.toolbar.Realize()
        self.SetToolBar(self.toolbar)
        #self.background_color = self.statusbar.GetBackgroundColour()
        #self.statusbar.SetBackgroundColour(self.background_color)
        #self.statusbar.SetBackgroundColour('RED')
        #self.statusbar.SetBackgroundColour('#E0E2EB')
        #self.statusbar.Refresh()
        
        self.Bind(wx.EVT_CLOSE, self.OnMenuQuit)


    def NewAnalysis(self, data, search_path="./"):
        """ Create new analysis object and show data """
        wx.BeginBusyCursor()
        anal = analysis.Analysis(data, search_path=search_path)
        # Get Plotting and Filtering parameters from previous analysis
        if hasattr(self, "analysis"):
            # Get Plotting and Filtering parameters from previous analysis
            fpar = self.analysis.GetParameters("Filtering")
            ppar = self.analysis.GetParameters("Plotting")
            newcfg = {"Filtering" : fpar,
                      "Plotting" : ppar  }
            # set colors if more than one:
            anal.SetParameters(newcfg)
            # reset contour accuracies
            anal.SetContourAccuracies()
            # set default contour colors
            anal.SetContourColors()
            # set contour colors with previous colors
            # - only works if len(colors) matches number of measurements
            colors = self.analysis.GetContourColors()
            anal.SetContourColors(colors)
            self.analysis._clear()
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
        info.SetWebSite(u"http://zellmechanik.com/")
        info.SetLicence(licence)
        info.SetIcon(misc.getMainIcon(pxlength=64))
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


    def OnMenuBatchFolder(self, e=None):
        batch.BatchFilterFolder(self, self.analysis)


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


    def OnMenuExportData(self, e=None):
        """ Export the event data of the entire analysis
        
        This will open a choice dialog for the user
        - which data (filtered/unfiltered)
        - which columns (Area, Deformation, etc)
        - to which folder should be exported 
        """
        # Generate dialog
        export.ExportAnalysisEventsTSV(self, self.analysis)


    def OnMenuExportPDF(self, e=None):
        """ Saves plot container as PDF
        
        Uses heuristic methods to resize
        - the plot
        - the scatter plot markers
        and then changes everything back
        """
        plot_export.export_plot_pdf(self)
        

    def OnMenuExportPNG(self, e=None):
        """ Saves plot container as png
        
        """
        plot_export.export_plot_png(self)


    def OnMenuExportStatistics(self, e=None):
        """ Saves statistics results from tab to text file
        
        """
        export.export_statistics_tsv(self)


    def OnMenuLoad(self, e=None, session_file=None):
        """ Load entire analysis """
        # Determine which session file to open
        if session_file is None:
            # User dialog
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
            fname = session_file 
        
        dirname = os.path.dirname(fname)
        self.config.SetWorkingDirectory(dirname)

        session.open_session(fname, self)
        

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
            
        # remove the autosaved file
        try:
            if os.path.exists(autosave.autosave_file):
                os.remove(autosave.autosave_file)
        except:
            pass
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
            session.save_session(path, self.analysis)
            return path
        else:
            dirname = dlg.GetDirectory()
            self.config.SetWorkingDirectory(dirname, name="Session")
            dlg.Destroy()


    def OnMenuSaveFull(self, e=None):
        """ Save configuration including measurement data """
        pass



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


