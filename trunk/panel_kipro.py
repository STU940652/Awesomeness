import wx
import wx.lib.scrolledpanel 
import time
import configparser
import threading
import Settings
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
                            self.setStopTime(None) # Prevent multiple calls
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

class PanelKipro (wx.lib.scrolledpanel.ScrolledPanel):
    kipro = None
    ShowingClip = False
    SavedAuxChannel = 0

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        self.infoBar = wx.InfoBar(self)
        self.parent = parent
        
        # Init the kipro stuff
        host = Settings.Config.get("KiPro","ip")
        if len(host):
            try:
                self.kipro = kipro.Client("http://" + host)
            except:
                self.kipro = None
            
        if self.kipro:
            self.infoBar.ShowMessage("Connected to KiPro")
        else:
            self.infoBar.ShowMessage("Kipro Offline")
            
        self.timecodeUpdateThread = None
        if self.kipro:
            self.timecodeUpdateThread = TimecodeUpdater("http://" + host, self, self.TimecodeCallback, self.OnEndClip)
            self.timecodeUpdateThread.start()
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(wx.StaticText(self, -1, "KiPro"))
        
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
                    #("<",   "Play Reverse Command"),
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
        self.Bind(wx.EVT_BUTTON, self.OnPlayTo, self.stopTimePlayToButton)        
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
        #wx.lib.scrolledpanel.ScrolledPanel.SetupScrolling(self)
        
        # Start a timer to get latest setting from kipro
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2e+3) # 2 second interval
    
    def OnCueClip (self, evt=None):
        if self.kipro:
            self.kipro.cueToTimecode(self.startTimeText.GetValue())
            
    def OnShowClip (self, evt):
        self.ShowingClip = True
        # Prep clip
        self.OnCueClip()
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(self.stopTimeText.GetValue())
            
        # Prep Video Switcher.  Set Preview to the correct channel
        self.parent.panelHS50.ChangeOutput('PVW', Settings.Config.get("HS50","KiProChannel"))
        
        # Video Switcher PGM Fade-to-Black
        self.parent.panelHS50.OnFTB()
        
        # Wait for fade to complete
        time.sleep(1)
        
        # Video Switcher: Get and store AUX channel
        self.SavedAuxChannel = self.parent.panelHS50.AUX_radio.GetSelection() # Returns number
        self.SavedAuxChannel = self.parent.panelHS50.AUX_radio.GetItemLabel(self.SavedAuxChannel) # Returns label
        
        # Video Switcher: AUX to PGM
        self.parent.panelHS50.ChangeOutput('AUX', 'PGM')
                
        # TODO: Audio Mixer: Fade Out
            
        # Start clip
        if self.kipro:
            self.kipro.play()
            
        # Video Switcher: Swap PGM/PVW and Un-Fade-to-Black
        self.parent.panelHS50.OnCut()
        self.parent.panelHS50.OnFTB()
        
        # TODO: Audio Mixer: Fade In
        
        # Side Projectors: Un-shutter
        self.parent.panelProjectors.SetShutter(False)
            
    def OnEndClip (self, evt=None):
    
        if self.ShowingClip:
            # Video Switcher: Fade-to-black
            self.parent.panelHS50.OnFTB()
            
            # TODO: Audio Mixer: Fade Out
            
            # Wait for fade to complete
            time.sleep(1)
            
            # Side Projectors: Shutter
            self.parent.panelProjectors.SetShutter(True)

            # Video Switcher: Restore AUX
            self.parent.panelHS50.ChangeOutput('AUX', self.SavedAuxChannel)
            
            # Video Switcher: Swap PGM/PVW and Un-Fade-to-Black
            self.parent.panelHS50.OnCut()
            self.parent.panelHS50.OnFTB()
            
        # Stop playback
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(None)
        if self.kipro:
            self.kipro.stop()
            
        ShowingClip = False
            
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
            
    def OnPlayTo (self, evt):
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(self.stopTimeText.GetValue())
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
            if self.playListCombobox.GetItems() != playlist:
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
        