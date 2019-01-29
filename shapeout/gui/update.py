#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.version import LooseVersion

import urllib2
import simplejson
import sys
import traceback
import webbrowser

import wx
import wx.lib.delayedresult as delayedresult

from .. import _version as so_version


def check_release(
            ghrepo="user/repo",
            version=None, timeout=20):
    """ Check GitHub repository for latest release
    """
    update = False
    msg = ""
    u = "https://api.github.com/repos/{}/releases/latest".format(ghrepo)
    web = "https://github.com/{}/releases".format(ghrepo)
    try:
        data = urllib2.urlopen(u, timeout=timeout).read()
    except:
        msg = "Timeout or wrong URL."
        try:
            with open("check_update_error.log", "w") as fe:
                fe.writelines(str(traceback.format_exc()))
        except:
            pass
    else:
        j = simplejson.loads(data)
        
        newversion = j["tag_name"]
        
        if version is not None:
            new = LooseVersion(newversion)
            old = LooseVersion(version)
            if new <= old:
                msg = "No update available."
            else:
                msg = web
                update = newversion
                # determine which URL we need
                if sys.platform.lower == "windows":
                    dlid = "win_32bit_setup.exe"
                else:
                    dlid = False
                # search for download file and replace msg
                if dlid:
                    for a in j["assets"]:
                        if a["browser_download_url"].count(dlid):
                            msg = a["browser_download_url"]
                    
    return update, msg

                
def Update(parent):
    """ This is a thread for _Update """
    ghrepo="ZELLMECHANIK-DRESDEN/ShapeOut"
    parent.StatusBar.SetStatusText("Checking for updates...")
    version = so_version.version
        
    delayedresult.startWorker(_UpdateConsumer, _UpdateWorker,
                              wargs=(ghrepo, version),
                              cargs=(parent,))


def _UpdateConsumer(delayedresult, parent):
    results = delayedresult.get()
    parent.StatusBar.SetStatusText("Update: "+results[1])
    if results[0]:
        updatemenu = wx.Menu()
        parent.menubar.Append(updatemenu, "&Update available!")
        menudl = updatemenu.Append(
                                wx.ID_ANY,
                                "Download version {}".format(results[0]),
                                results[1])
        def get_update(e=None, url=results[1]):
            webbrowser.open(url)
            
        parent.Bind(wx.EVT_MENU, get_update, menudl)
    parent.StatusBar.SetStatusText("")


def _UpdateWorker(*args):
    results = check_release(*args)
    return results
