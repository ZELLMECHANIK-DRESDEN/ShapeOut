#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Shape-Out - gauge frame class"""
from __future__ import division, print_function

import platform
import time

import multiprocessing as mp
import threading as td
import wx


# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()



def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


def dummywait(arg=None):
    """ a long-running function """
    while True:
        time.sleep(.5)


def longfunction(arg=None):
    """ a long-running function """
    time.sleep(2)
    return("{} and peter".format(arg))



########################################################################
class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data



########################################################################
class WorkerThread(td.Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window, longfunction, func_args,
                 post_call, post_call_kwargs, worker_id=8472, msg=""):
        """Init Worker Thread Class."""
        td.Thread.__init__(self)
        self._notify_window = notify_window
        self._longfunction = longfunction
        self._func_args = func_args
        self._post_call = post_call
        self._post_call_kwargs = post_call_kwargs
        self._worker_id = worker_id
        self._msg=msg
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()


    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        # a long process (well, 10s here) as a simple loop - you will
        # need to structure your processing so that you periodically
        # peek at the abort variable
        self.pool = mp.Pool(processes = 1)
        result = self.pool.apply_async(self._longfunction, self._func_args)

        while True:
            lc = len(mp.active_children())
            try:
                res=result.get(timeout=.1)
            except mp.TimeoutError:
                if lc==0:
                    wx.PostEvent(self._notify_window,
                                 ResultEvent((None,None,None,
                                              self._worker_id)
                                            )
                                )
                    break
            else:
                # Here's where the result would be returned (this is an
                # example fixed result of the number 10, but it could be
                # any Python object)
                wx.PostEvent(self._notify_window,
                             ResultEvent((
                                          self._post_call,
                                          self._post_call_kwargs,
                                          res,
                                          self._worker_id
                                          )
                                        )
                            )
                break
        

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self.pool.terminate()



########################################################################
class GaugeFrame(wx.Frame):
    """Class MainFrame."""
    def __init__(self, *args, **kwargs):
        """ A frame that has a gauge in the statusbar with functionality
        
        The function `GaugeIndefiniteStart` can be used to run functions
        in the background (separate process) while the frontend still
        responds to user input. While the function is running, a gauge
        is displayed in the status bar.
        
        Multiple functions can be run at the same time by specifying
        ther keyworkd argument `worker_id` in `GaugeIndefiniteStart`.
        
        """
        super(GaugeFrame, self).__init__(*args, **kwargs)
        self._verbose=False

        # Set up event handler for any worker thread results
        EVT_RESULT(self, self._OnResult)

        # And indicate we don't have a worker thread yet
        self.workers = dict()
        
        ## Status Bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(4)
        self.statusbar.SetStatusWidths([250, 150, -1, -2])
        self.statusbar.SetStatusStyles([0,1,0,0])
        # progress bar
        self.gauge = wx.Gauge(self.statusbar, -1, 50, style=wx.GA_HORIZONTAL)
        # position and size of progress bar
        rect = self.statusbar.GetFieldRect(1)
        posx = rect.x
        posy = rect.y
        width = rect.width
        height = rect.height
        if platform.system()=="Linux":
            posy += self.statusbar.GetBorderY()
        self.gauge.SetPosition((posx, posy))
        self.gauge.SetSize((width, height))
        # hide progress bar initially
        self.gauge.Hide()

        self._timer = wx.Timer(self)


    def GaugeIndefiniteStart(self, event=None, func=dummywait,
                             func_args=(), post_call=None, 
                             post_call_kwargs = {},
                             msg="", worker_id=8472):
        """Start a long running function (worker)
        
        Parameters
        ----------
        event : any
            reserved
        func : callable
            The long running function to be computed.
        func_args : tuple
            Arguments for `func`.
        post_call : callable or None
            When `func` is finished, calls this function with the
            return value of `func`.
        post_call_kwargs : dict
            Keyword arguments for the post_call function.
        msg : str
            A message displayed in the statusbar of the gauge frame.
        worker_id : dictionary key
            A worker id. Setting different `worker_id` values for
            different tasks can be used to parallelize them. If the
            `worker_id` is always the same (e.g. 8472), then only one
            worker can be run at a time. Subsequent calls with the same
            `worker_id` to `GaugeIndefiniteStart` will kill the spawned
            worker and start a new one.
        
        
        Returns
        -------
        None
        
        
        See Also
        --------
        `GaugeIndefiniteStop` - stop execution of a worker


        Notes
        -----
        - `self._TimerHandler` makes the gauge pulse
        - `self._OnResult` calls `post_call`

        """
        # Trigger the worker thread unless it's already busy
        if self.workers.has_key(worker_id):
            self.GaugeIndefiniteStop(worker_id=worker_id)
        self.gauge.Show()
        self.Bind(wx.EVT_TIMER, self._TimerHandler)
        self._timer.Start(200)
        if self._verbose:
            print('Starting computation')
        self.workers[worker_id] = WorkerThread(self, 
                                               longfunction=func,
                                               func_args=func_args,
                                               post_call=post_call,
                                               post_call_kwargs=post_call_kwargs,
                                               worker_id=worker_id,
                                               msg=msg
                                              )


    def GaugeIndefiniteStop(self, event=None, worker_id=8472):
        """ Abort computation of a worker
        
        Parameters
        ----------
        worker_id : dictionary key  
            The specific worker to be stopped.


        Returns
        -------
        None
        
        
        See Also
        --------
        `GaugeIndefiniteStart` - start execution of a worker
        """
        # Flag the worker thread to stop if running
        if self.workers.has_key(worker_id):
            if self._verbose:
                print('Stopping gauge')
            worker = self.workers.pop(worker_id)
            worker.abort()
        # Before ending the gauge, check if there are other workers.
        if len(self.workers) == 0:
            self.gauge.Hide()
            self._timer.Stop()
            self.Unbind(wx.EVT_TIMER)


    def _OnResult(self, event):
        """Show Result status."""
        func = event.data[0]
        kwargs = event.data[1]
        args = event.data[2]
        worker_id = event.data[3]
        self.GaugeIndefiniteStop(worker_id)
        if callable(func):
            func(args, **kwargs)
            if self._verbose:
                print("Result:", event.data)
        else:
            if self._verbose:
                print("Computation aborted")


    def _TimerHandler(self, event):
        """Keep the gauge pulsing"""
        ## TODO
        # - display progress for workers that have progress
        # - display worker messages in statusbar
        self.gauge.Show()
        self.gauge.Pulse()


########################################################################
########################################################################

if __name__ == '__main__':
    class ZZTestGauge(GaugeFrame):
        def __init__(self, *args, **kwargs):
            GaugeFrame.__init__(self, *args, **kwargs)
            self._verbose = True
            # Dumb sample frame with two buttons
            wx.Button(self, ID_START, 'Start', pos=(0,0))
            wx.Button(self, ID_STOP, 'Stop', pos=(0,50))
            self.status = wx.StaticText(self, -1, '', pos=(0,100))

            self.Bind(wx.EVT_BUTTON, self.ComputeSomething, id=ID_START)
            self.Bind(wx.EVT_BUTTON, self.GaugeIndefiniteStop, id=ID_STOP)
        
        def ComputeSomething(self, event=None):
            self.status.SetLabel("Started Computation.")
            self.GaugeIndefiniteStart(func=longfunction, func_args=("hans",),
                                 post_call=self.ProcessResults)
                                 
            
        def ProcessResults(self, data):
            self.status.SetLabel("Computation Result: {}".format(data))


    # Button definitions
    ID_START = wx.NewId()
    ID_STOP = wx.NewId()

    app = wx.App()
    app.frame = ZZTestGauge(None, -1, "Gauge Test")
    app.frame.Show(True)
    app.SetTopWindow(app.frame)

    app.MainLoop()



