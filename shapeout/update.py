#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.version import LooseVersion

import requests
import simplejson
import sys

import webbrowser
import wx
import wx.lib.delayedresult as delayedresult

import _version as so_version

def check_release(
            ghrepo="user/repo",
            version=None, timeout=5):
    """ Check GitHub repository for latest release
    """
    update = False
    msg = ""
    u = "https://api.github.com/repos/{}/releases/latest".format(ghrepo)
    web = "https://github.com/{}/releases".format(ghrepo)
    try:
        data = requests.get(u, timeout=timeout)
    except:
        msg = "timeout"
    else:
        if not data.ok:
            msg = "url error"
        else:
            j = simplejson.loads(data.content)
            
            newversion = j["tag_name"]
            
            if version is not None:
                new = LooseVersion(newversion)
                old = LooseVersion(version)
                if new <= old:
                    msg = "no update available"
                else:
                    update = newversion
                    # determine which URL we need
                    if sys.platform.lower == "windows":
                        dlid = "win_32bit_setup.exe"
                    else:
                        dlid = False
                    # search for download file
                    if dlid:
                        for a in j["assets"]:
                            if a["browser_download_url"].count(dlid):
                                msg = a["browser_download_url"]
                    else:
                        msg = web
    return update, msg
                
def Update(parent):
    """ This is a thread for _Update """
    ghrepo="ZellMechanik-Dresden/ShapeOut"
    parent.StatusBar.SetStatusText("Connecting to server...")
    if hasattr(so_version, "repo_tag"):
        version = so_version.repo_tag  # @UndefinedVariable
    else:
        version = so_version.version
        
    delayedresult.startWorker(_UpdateConsumer, _UpdateWorker,
                              wargs=(ghrepo, version),
                              cargs=(parent,))

def _UpdateConsumer(delayedresult, parent):
    results = delayedresult.get()
    #dlg = UpdateDlg(parent, results)
    #dlg.Show()
    if results[0]:
        
        updatemenu = wx.Menu()
        parent.menubar.Append(updatemenu, _('&Update available!'))
        menudl = updatemenu.Append(
                                wx.ID_ANY,
                                _("Download version {}").format(results[0]),
                                results[1])
        
        def get_update(e=None, url=results[1]):
            webbrowser.open(url)
            
        parent.Bind(wx.EVT_MENU, get_update, menudl)

def _UpdateWorker(*args):
    results = check_release(*args)
    return results
