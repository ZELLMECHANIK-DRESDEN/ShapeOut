#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - wx frontend components"""
from __future__ import division, print_function, unicode_literals

import os
import platform
import pkg_resources
import sys
import traceback

import imageio.plugins.ffmpeg as imioff
import numpy as np
import wx


import dclab


from .. import analysis
from ..settings import SettingsFile
from .. import meta_tool

from . import autosave
from . import batch
from .controls import ControlPanel
from .explorer import ExplorerPanel
from . import export
from . import gaugeframe
from . import help
from . import misc
from . import plot_export
from . import plot_main
from . import session_ui
from . import update
from . import video



class ExceptionDialog(wx.MessageDialog):
    """"""
    def __init__(self, msg):
        """Constructor"""
        wx.MessageDialog.__init__(self, None, msg, "Error", wx.OK|wx.ICON_ERROR)



class Frame(gaugeframe.GaugeFrame):
    """"""
    def __init__(self, version):
        """Constructor"""
        self.config = SettingsFile()
        self.version = version
        #size = (1300,900)
        size = (1200,700)
        minsize = (900, 700)
        gaugeframe.GaugeFrame.__init__(self, None, -1,
                title = "Shape-Out - version {}".format(version),
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
        ddict = {"area_um" : np.linspace(45, 250, 10),
                 "deform" : np.arange(10)*.02}
        cfg = {"setup": {"channel width": 20},
               "imaging": {"pixel size": 0.34}}
        rtdc_ds = dclab.new_dataset(ddict)
        rtdc_ds.config.update(cfg)
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
        - download ffmpeg
        """
        # Check if we have an autosaved session that we did not delete
        recover = autosave.check_recover(self)
        
        # Load session file if provided
        if session_file is not None and not recover:
            self.OnMenuLoad(session_file=session_file)

        if self.config.get_bool("check update"):
            # Search for updates
            update.Update(self)

        if self.config.get_bool("autosave session"):
            # Start autosaving
            autosave.autosave_run(self)

        # download ffmpeg for imageio
        try:
            imioff.get_exe()
        except imioff.NeedDownloadError:
            # Tell the user that we will download ffmpeg now!
            msg = "Shape-Out needs to download `FFMPEG` in order " \
                 +"to display and export video data. Please make " \
                 +"sure you are connected to the internet and " \
                 +"click OK. Depending on your connection, this " \
                 +"may take a while. Please be patient. There " \
                 +"is no progress dialog."
            dlg = wx.MessageDialog(parent=None,
                                   message=msg, 
                                   caption="FFMPEG download",
                                   style=wx.OK|wx.CANCEL|wx.ICON_QUESTION)

            if dlg.ShowModal() == wx.ID_OK:
                imioff.download()



    def InitUI(self):
        """Menus, Toolbar, Statusbar"""
        
        ## Menubar
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        
        ## File menu
        fileMenu = wx.Menu()
        self.menubar.Append(fileMenu, "&File")
        # data
        fpath = fileMenu.Append(wx.ID_REPLACE, "Find Measurements", 
                                "Select data file location")
        self.Bind(wx.EVT_MENU, self.OnMenuSearchPath, fpath)
        fpathadd = fileMenu.Append(wx.ID_FIND, "Add Measurements", 
                                "Select data file location")
        self.Bind(wx.EVT_MENU, self.OnMenuSearchPathAdd, fpathadd)
        # clear measurements
        fpathclear = fileMenu.Append(wx.ID_CLEAR, "Clear Measurements", 
                             "Clear unchecked items in project list")
        self.Bind(wx.EVT_MENU, self.OnMenuClearMeasurements, fpathclear)
        fileMenu.AppendSeparator()
        # save
        fsave = fileMenu.Append(wx.ID_SAVE, "Save Session", 
                                "Select .zmso file")
        self.Bind(wx.EVT_MENU, self.OnMenuSave, fsave)
        # load
        fload = fileMenu.Append(wx.ID_OPEN, "Open Session", 
                                "Select .zmso file")
        self.Bind(wx.EVT_MENU, self.OnMenuLoad, fload)
        fileMenu.AppendSeparator()
        # quit
        fquit = fileMenu.Append(wx.ID_EXIT, "Quit", 
                                "Quit Shape-Out")
        self.Bind(wx.EVT_MENU, self.OnMenuQuit, fquit)
        
        ## Export Data menu
        exportDataMenu = wx.Menu()
        self.menubar.Append(exportDataMenu, "Export &Data")
        e2fcs = exportDataMenu.Append(wx.ID_ANY, "All &event data (*.fcs)", 
                "Export all scalar event data as flow cytometry standard files")
        self.Bind(wx.EVT_MENU, self.OnMenuExportEventsFCS, e2fcs)
        if self.config.get_bool("expert mode"):
            # Only allow .rtdc export in expert mode
            e2rtdc = exportDataMenu.Append(wx.ID_ANY, "All &event data (*.rtdc)", 
                    "Export all event data as .rtdc files")
            self.Bind(wx.EVT_MENU, self.OnMenuExportEventsRTDC, e2rtdc)
        e2tsv = exportDataMenu.Append(wx.ID_ANY, "All &event data (*.tsv)", 
                "Export all scalar event data as tab-separated values")
        self.Bind(wx.EVT_MENU, self.OnMenuExportEventsTSV, e2tsv)
        e2stat = exportDataMenu.Append(wx.ID_ANY, "Computed &statistics (*.tsv)", 
                       "Export the statistics data as tab-separated values")
        self.Bind(wx.EVT_MENU, self.OnMenuExportStatistics, e2stat)
        e2avi = exportDataMenu.Append(wx.ID_ANY, "All &event images (*.avi)", 
                "Export the event images as video files")
        self.Bind(wx.EVT_MENU, self.OnMenuExportEventsAVI, e2avi)
        
        ## Export Plot menu
        exportImgMenu = wx.Menu()
        self.menubar.Append(exportImgMenu, "Export &Image")

        graph2pdf = exportImgMenu.Append(
                        wx.ID_ANY,
                        "Graphical &plot (*.pdf)", 
                        "Export the plot as a portable document file")
        self.Bind(wx.EVT_MENU, self.OnMenuExportPDF, graph2pdf)
        
        event2imgc = exportImgMenu.Append(
                        wx.ID_ANY,
                        "Event image &with contour (*.png)", 
                        "Export current event image including contour")
        self.Bind(wx.EVT_MENU,
                  lambda event: self.OnMenuExportEventImagePNG(event, contour=True),
                  event2imgc)

        event2imgnc = exportImgMenu.Append(
                        wx.ID_ANY,
                        "Event image with&out contour (*.png)", 
                        "Export current event image excluding contour")
        self.Bind(wx.EVT_MENU,
                  lambda event: self.OnMenuExportEventImagePNG(event, contour=False),
                  event2imgnc)
        
        # export SVG disabled:
        # The resulting graphic is not better than the PDF and axes are missing
        #e2svg = exportPlotMenu.Append(wx.ID_ANY, "Graphical &plot (*.svg)", 
        #               "Export the plot as a scalable vector graphics file")
        #self.Bind(wx.EVT_MENU, self.OnMenuExportSVG, e2svg)
        # export PNG disabled:
        # https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut/issues/62
        #e2png = exportMenu.Append(wx.ID_ANY, "Graphical &plot (*.png)", 
        #               "Export the plot as a portable network graphic")
        #self.Bind(wx.EVT_MENU, self.OnMenuExportPNG, e2png)


        ## Batch menu
        batchMenu = wx.Menu()
        self.menubar.Append(batchMenu, "&Batch")
        b_filter = batchMenu.Append(wx.ID_ANY, "&Statistical summary",
            "Assemble a statistical summary for multiple datasets on disk.")
        self.Bind(wx.EVT_MENU, self.OnMenuBatchFolder, b_filter)

        ## Preferences menu
        prefMenu = wx.Menu()
        self.menubar.Append(prefMenu, "&Preferences")
        self.menuAutosave = prefMenu.AppendCheckItem(wx.ID_ANY,
                                                     "&Autosave session",
                                    "Autosave session in the background")
        self.menuAutosave.Check(self.config.get_bool("autosave session"))
        self.menuSearchUpdate = prefMenu.AppendCheckItem(wx.ID_ANY,
                                                    "&Check for updates",
                                      "Check for new version on startup")
        self.menuSearchUpdate.Check(self.config.get_bool("check update"))
        self.menuExpert = prefMenu.AppendCheckItem(wx.ID_ANY,
                                                   "&Expert mode",
                                "Enable advanced functionalities")
        self.menuExpert.Check(self.config.get_bool("expert mode"))
        for item in prefMenu.GetMenuItems():
            self.Bind(wx.EVT_MENU, self.OnMenuPreferences, item)
        
        ## Help menu
        helpmenu = wx.Menu()
        self.menubar.Append(helpmenu, "&Help")
        menuDocs = helpmenu.Append(wx.ID_ANY, "&Documentation",
                        "View the online documentation in your webbrowser")
        self.Bind(wx.EVT_MENU, self.OnMenuHelpDocs, menuDocs)
        menuSoftw = helpmenu.Append(wx.ID_ANY, "&Software",
                                    "Information about the software used")
        self.Bind(wx.EVT_MENU, self.OnMenuHelpSoftware, menuSoftw)
        menuAbout = helpmenu.Append(wx.ID_ABOUT, "&About",
                                    "Information about this program")
        self.Bind(wx.EVT_MENU, self.OnMenuHelpAbout, menuAbout)

        ## Toolbar
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT|wx.TB_HORIZONTAL|wx.TB_NODIVIDER)
        iconsize = (36,36)
        self.toolbar.SetToolBitmapSize(iconsize)
        
        names = [['Load Measurements', wx.ID_REPLACE, wx.ART_FIND_AND_REPLACE],
                 ['Add Measurements', wx.ID_FIND, wx.ART_FIND],
                 ['Save Session', wx.ID_SAVE, wx.ART_FILE_SAVE_AS],
                 ['Open Session', wx.ID_OPEN, wx.ART_FILE_OPEN],
                ]
        
        def add_icon(name):
            self.toolbar.AddLabelTool(name[1],
                                      name[0],
                                      bitmap=wx.ArtProvider.GetBitmap(
                                                                  name[2],
                                                                  wx.ART_TOOLBAR,
                                                                  iconsize))
        
        def add_image(name, height=-1, width=-1):
            png = wx.Image(name, wx.BITMAP_TYPE_ANY)
            image = wx.StaticBitmap(self.toolbar, -1, png.ConvertToBitmap(), size=(width,height))
            self.toolbar.AddControl(image)
        
        for name in names:
            add_icon(name)

        imdir = pkg_resources.resource_filename("shapeout", "img")
        add_image(os.path.join(imdir, "transparent_h50.png"),
                  width=75,
                  height=iconsize[0])
        add_image(os.path.join(imdir, "zm_logo_h36.png"))        

        try:
            # This only works with wxPython3
            self.toolbar.AddStretchableSpace()
        except:
            pass

        add_image(os.path.join(imdir, "shapeout_logotype_h36.png"))

        try:
            # This only works with wxPython3
            self.toolbar.AddStretchableSpace()
        except:
            pass
        
        add_image(os.path.join(imdir, "transparent_h50.png"),
                  height=iconsize[0])
        add_icon(['Quit', wx.ID_EXIT, wx.ART_QUIT])
        self.toolbar.Realize()
        self.SetToolBar(self.toolbar)
        #self.background_color = self.statusbar.GetBackgroundColour()
        #self.statusbar.SetBackgroundColour(self.background_color)
        #self.statusbar.SetBackgroundColour('RED')
        #self.statusbar.SetBackgroundColour('#E0E2EB')
        #self.statusbar.Refresh()
        
        self.Bind(wx.EVT_CLOSE, self.OnMenuQuit)


    def NewAnalysis(self, data):
        """Create new analysis object and show data """
        wx.BeginBusyCursor()
        # Get Plotting and Filtering parameters from previous analysis
        newcfg = {}
        if hasattr(self, "analysis"):
            # Get Plotting and Filtering parameters from previous analysis
            for key in ["analysis", "calculation", "filtering", "plotting"]:
                try:
                    newcfg[key] = self.analysis.GetParameters(key)
                except IndexError:
                    pass
            # Remember contour colors
            contour_colors = self.analysis.GetContourColors()
            self.analysis._clear()
        else:
            contour_colors = None

        # Set Analysis
        anal = analysis.Analysis(data, config=newcfg)
        # Reset plotting parameters
        anal.reset_plot()
        # Set previous contour colors
        anal.SetContourColors(contour_colors)

        self.analysis = anal
        self.PanelTop.NewAnalysis(anal)
        self.PlotArea.Plot(anal)
        wx.EndBusyCursor()


    def OnMenuBatchFolder(self, e=None):
        return batch.BatchFilterFolder(self, self.analysis)


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

    def OnMenuExportEventImagePNG(self, e=None, contour=False):
        """Export the currently visible event image
        
        The `contour` parameter allows to dis/en-able plotting
        the contour as well.
        """
        # Get image
        image = self.ImageArea.GetImage(contour=contour)
        export.export_event_image_png(self, image)


    def OnMenuExportEventsAVI(self, e=None):
        """Export the event image data to an avi file
        
        This will open a dialog for the user to select
        the target file name.
        """
        # Generate dialog
        export.export_event_images_avi(self, self.analysis)


    def OnMenuExportEventsFCS(self, e=None):
        """Export the event data of the entire analysis as fcs
        
        This will open a choice dialog for the user
        - which data (filtered/unfiltered)
        - which features (area_um, deform, etc)
        - to which folder should be exported 
        """
        # Generate dialog
        export.ExportAnalysisEventsFCS(self, self.analysis)


    def OnMenuExportEventsRTDC(self, e=None):
        """Export the event data of the entire analysis as rtdc
        
        This will open a choice dialog for the user
        - which data (filtered/unfiltered)
        - which features (area_um, deform, etc)
        - to which folder should be exported 
        """
        # Generate dialog
        export.ExportAnalysisEventsRTDC(self, self.analysis)


    def OnMenuExportEventsTSV(self, e=None):
        """Export the event data of the entire analysis as tsv
        
        This will open a choice dialog for the user
        - which data (filtered/unfiltered)
        - which features (area_um, deform, etc)
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


    def OnMenuExportSVG(self, e=None):
        """ Saves plot container as SVG
        
        Uses heuristic methods to resize
        - the plot
        - the scatter plot markers
        and then changes everything back
        """
        plot_export.export_plot_svg(self)


    def OnMenuExportPNG(self, e=None):
        """ Saves plot container as png
        
        """
        plot_export.export_plot_png(self)


    def OnMenuExportStatistics(self, e=None):
        """ Saves statistics results from tab to text file
        
        """
        export.export_statistics_tsv(self)


    def OnMenuHelpAbout(self, e=None):
        help.about()

    def OnMenuHelpDocs(self, e=None):
        help.docs()
    
    def OnMenuHelpSoftware(self, e=None):
        help.software()


    def OnMenuLoad(self, e=None, session_file=None):
        """ Load entire analysis """
        session_ui.open_session(self, session_file=session_file)


    def OnMenuPreferences(self, event):
        """Update configuration file and display restart messages"""
        val = event.Checked()
        eid = event.Id
        display_name = ""
        if eid == self.menuAutosave.Id:
            self.config.set_bool("autosave session", val)
            display_name = "Session autosaving"
        elif eid == self.menuExpert.Id:
            self.config.set_bool("expert mode", val)
            display_name = "Expert mode"
        elif eid == self.menuSearchUpdate.Id:
            self.config.set_bool("check update", val)
        else:
            raise ValueError("Unknown preferences event!")

        if display_name:
            if val:
                disen = "enabled"
            else:
                disen = "disabled"
            msg = "{} will be {} on next run.".format(display_name, disen)
            caption = "{} {}.".format(display_name, disen)
            dlg = wx.MessageDialog(self, msg, caption,
                                   wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()


    def OnMenuSearchPath(self, e=None):
        """ Set path of working directory
        
        Display Dialog to select folder and update Content of PanelLeft.
        This calls `PanelLeft.SetProjectTree`.
        """
        dlg = wx.DirDialog(self, "Please select a directory",
               defaultPath=self.config.get_path(name="MeasurementList"))
        answer = dlg.ShowModal()
        if answer == wx.ID_OK:
            path = dlg.GetPath().encode("utf-8")
            self.config.set_path(path, name="MeasurementList")
            dlg.Destroy()
            self.GaugeIndefiniteStart(
                                func=meta_tool.collect_data_tree,
                                func_args=(path,),
                                post_call=self.PanelLeft.SetProjectTree,
                                msg="Searching for data files"
                                )


    def OnMenuSearchPathAdd(self, e=None, add=True, path=None,
                            marked=[]):
        """ Convenience wrapper around OnMenuSearchPath"""
        if path is None:
            dlg = wx.DirDialog(self, "Please select a directory",
                   defaultPath=self.config.get_path(name="MeasurementList"))
            answer = dlg.ShowModal()
            path = dlg.GetPath().encode("utf-8")
            self.config.set_path(path, name="MeasurementList")
            dlg.Destroy()
            if answer != wx.ID_OK:
                return
        self.GaugeIndefiniteStart(
                        func=meta_tool.collect_data_tree,
                        func_args=(path,),
                        post_call=self.PanelLeft.SetProjectTree,
                        post_call_kwargs = {"add":add, "marked":marked},
                        msg="Searching for data files"
                        )

    def OnMenuQuit(self, e=None):
        if hasattr(self, "analysis") and self.analysis is not None:
            # Ask to save the session
            dial = wx.MessageDialog(self, 
                'Do you want to save the current Session?', 
                'Save Session?', 
                 wx.ICON_QUESTION | wx.CANCEL | wx.YES_NO | wx.NO_DEFAULT )
            self._quit_dialog = dial
            result = dial.ShowModal()
            dial.Destroy()
            if result == wx.ID_CANCEL:
                return # abort
            elif result == wx.ID_YES:
                filename = self.OnMenuSave()
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


    def OnMenuSave(self, e=None):
        """ Save configuration without measurement data """
        session_ui.save_session(self)


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
