import wx
import time
import configparser
import threading
from AJArest import kipro

class ButtonWithData (wx.Button):
    Data = None
    
    def SetData (self, data):
        self.Data = data
        
    def GetData (self):
        return self.Data
        
class TimecodeUpdater(threading.Thread):
    __doc__ = """
    This listener creates a connection to a ki-pro unit and listens for timecode event updates.
    WARNING: Timecode events may not occur every frame. If you need a frame accurate timecode, consider using
    RS422 or setting timecode as a record trigger.

    quickstart:

    python$
      >>> from aja.embedded.rest.kipro import *
      >>> l = TimecodeListener('http://YourKiPro')
      >>> l.start()
      >>> print l.getTimecode()
    """

    def __init__(self, url, gui, timecode_callback, stopshow_callback = None):
        """
        Create a TimecodeUpdater.
        Use start() to start it listening.
        """
        super(TimecodeUpdater, self).__init__()
        self.url = url
        self.__timecode = ""
        self.__stop = False
        self.__lock = threading.RLock()
        self.__gui = gui
        self.__timecode_callback = timecode_callback
        self.__stopshow_callback = stopshow_callback
        self.__stopcode = None

    def run(self):
        c = kipro.Client(self.url)
        connection = c.connect()
        if connection:
            while not self.__stop:
                try:
                    # See if the GUI closed.  This will throw an exception if the GUI is closed.
                    self.__gui.IsBeingDeleted()

                    events = c.waitForConfigEvents(connection)
                    for event in events:
                        if (event["param_id"] == "eParamID_DisplayTimecode"):
                            # Update timecode in main loop
                            
                            wx.CallAfter(self.__timecode_callback, event["str_value"])
                            timecode =  event["str_value"]
                            break
                            
                    if self.__stopcode and self.__stopshow_callback:
                        if timecode > self.__getStopTime():
                            wx.CallAfter(self.__stopshow_callback)
                            
                except:
                    break
            print("Listener stopping.")
        else:
            print("Failed to connect to", self.url)

    def stop(self):
        """ Tell the listener to stop listening and the thread to exit. """
        with self.__lock:
            self.__stop = True
            
    def setStopTime(self, timecode):
        """ Threadsafe. """
        with self.__lock:
            self.__stopcode = timecode

    def __getStopTime(self):
        """ Thread safe. """
        with self.__lock:
            return self.__stopcode

class PanelKipro (wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        self.infoBar = wx.InfoBar(self)
        
        # Init the kipro stuff
        #try:
        #    self.kipro = kipro.Client("http://10.70.58.26")
        #except:
        self.kipro = None
            
        if self.kipro:
            self.infoBar.ShowMessage("Connected to KiPro")
        else:
            self.infoBar.ShowMessage("Kipro Offline")
            
        self.timecodeUpdateThread = None
        if self.kipro:
            self.timecodeUpdateThread = TimecodeUpdater("http://10.70.58.26", self, self.TimecodeCallback, self.OnEndClip)
            self.timecodeUpdateThread.start()
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.playListCombobox = wx.ComboBox(self, style = wx.CB_READONLY|wx.CB_DROPDOWN,)
        sizer.Add(self.playListCombobox, proportion = 1, flag=wx.EXPAND)
        self.cuePlaylistButton = wx.Button (self, -1, "Select")
        self.Bind(wx.EVT_BUTTON, self.OnSelectClipButton, self.cuePlaylistButton)
        sizer.Add(self.cuePlaylistButton)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Current Clip"))
        self.currentClipText = wx.TextCtrl (self, style = wx.TE_READONLY)
        sizer.Add(self.currentClipText, proportion = 1, flag=wx.EXPAND)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Current Time"))
        self.currentTimeText = wx.TextCtrl (self, style = wx.TE_READONLY, value = "00:12:00.000")
        sizer.Add(self.currentTimeText, flag=wx.EXPAND)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Current State"))
        self.currentStateText = wx.TextCtrl (self, style = wx.TE_READONLY)
        sizer.Add(self.currentStateText, flag=wx.EXPAND)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons = ( ("<<",  "Fast Reverse"),
                    ("<",   "Play Reverse Command"),
                    ("|<",  "Single Step Reverse"),
                    ("X",   "Stop Command"),
                    (">|",  "Single Step Forward"),
                    (">",   "Play Command"),
                    (">>",  "Fast Forward") )
        for buttonLable, buttonCommand in buttons:
            button = ButtonWithData(self, -1, buttonLable, size = (30,-1))
            button.SetData(buttonCommand)
            self.Bind(wx.EVT_BUTTON, self.OnTransportButton, button)
            sizer.Add(button)        
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.FlexGridSizer(cols = 5)
        sizer.Add(wx.StaticText(self, -1, "Start Time"))
        self.startTimeText = wx.TextCtrl (self, value = "00:00:00.000")
        sizer.Add(self.startTimeText, proportion = 1, flag=wx.EXPAND)
        self.startTimeFillButton = wx.Button (self, -1, "Fill")
        self.Bind(wx.EVT_BUTTON, self.OnFillStartTime, self.startTimeFillButton)
        sizer.Add(self.startTimeFillButton)
        self.startTimeCueButton = wx.Button (self, -1, "Cue")
        self.Bind(wx.EVT_BUTTON, self.OnCueStart, self.startTimeCueButton)
        sizer.Add(self.startTimeCueButton)
        self.startTimePlayFromButton = wx.Button (self, -1, "Play From")
        self.Bind(wx.EVT_BUTTON, self.OnPlayFrom, self.startTimePlayFromButton)
        sizer.Add(self.startTimePlayFromButton)
        
        sizer.Add(wx.StaticText(self, -1, "Stop Time"))
        self.stopTimeText = wx.TextCtrl (self, value = "00:00:00.000")
        sizer.Add(self.stopTimeText, proportion = 1, flag=wx.EXPAND)
        self.stopTimeFillButton = wx.Button (self, -1, "Fill")
        self.Bind(wx.EVT_BUTTON, self.OnFillStopTime, self.stopTimeFillButton)
        sizer.Add(self.stopTimeFillButton)
        sizer.AddStretchSpacer()
        self.stopTimePlayToButton = wx.Button (self, -1, "Play To")
        sizer.Add(self.stopTimePlayToButton)        
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
                
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cueClipButton = wx.Button (self, -1, "Cue Clip")
        self.Bind(wx.EVT_BUTTON, self.OnCueClip, self.cueClipButton)
        sizer.Add(self.cueClipButton)
        self.showClipButton = wx.Button (self, -1, "Show Clip")
        self.Bind(wx.EVT_BUTTON, self.OnShowClip, self.showClipButton)
        sizer.Add(self.showClipButton)
        self.cancelClipButton = wx.Button (self, -1, "Cancel Clip")
        self.Bind(wx.EVT_BUTTON, self.OnEndClip, self.cancelClipButton)
        sizer.Add(self.cancelClipButton)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        panelSizer.AddStretchSpacer()
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from kipro
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2e+3) # 2 second interval
    
    def OnCueClip (self, evt=None):
        if self.kipro:
            self.kipro.cueToTimecode(self.startTimeText.GetValue())
            
    def OnShowClip (self, evt):
        self.OnCueClip()
        if self.kipro:
            self.kipro.play()
            
    def OnEndClip (self, evt=None):
        if self.kipro:
            self.kipro.stop()
            
    def OnSelectClipButton (self, evt):
        if self.kipro:
            self.kipro.goToClip(self.playListCombobox.GetValue())

    def OnTransportButton (self, evt=None):
        command = evt.GetEventObject().GetData()
        if self.kipro:
            self.kipro.sendTransportCommandByDescription(command)
            
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(None)
            
    def OnCueStart (self, evt=None):
        if self.kipro:
            self.kipro.cueToTimecode(self.startTimeText.GetValue())

    def OnPlayFrom (self, evt):
        self.OnCueStart()
        if self.kipro:
            self.kipro.play()
            
    def OnTimer (self, evt):
        if self.kipro:
            # Get the playlists
            playlist = []
            playlistDictList = self.kipro.getPlaylists()
            for playlistDist in playlistDictList:
                if playlistDist["name"]=='All Clips':
                    playlist = playlistDist["cliplist"]
                    break
            self.playListCombobox.SetItems(playlist)
            
            # Get the current clip name
            self.currentClipText.SetValue(self.kipro.getCurrentClipName())
            
            # Get the current transport state
            self.currentStateText.SetValue(self.kipro.getTransporterState()[1])
            
    def OnFillStartTime (self, evt):
        self.startTimeText.SetValue(self.currentTimeText.GetValue())
            
    def OnFillStopTime (self, evt):
        self.stopTimeText.SetValue(self.currentTimeText.GetValue())
        
    def TimecodeCallback (self, timecode):
        self.currentTimeText.SetValue(timecode)
        
