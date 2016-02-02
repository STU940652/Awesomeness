import wx
import wx.lib.scrolledpanel 
import time
import configparser
import threading
import Settings
from AJArest import kipro

# Time conversion helper
def frames_to_timecode (frames, fps, hms_only = False):
    frames = float(frames)
    h = int(frames/(60*60*fps))
    msl = frames - h*60*60*fps
    m = int(msl/(60*fps))
    msl = msl - m*60*fps
    s = int(msl/fps)
    f = round(msl-s*fps)
    if hms_only:
        return "%02i:%02i:%02i" % (h,m,s)
    return "%02i:%02i:%02i:%02i" % (h,m,s,f)
    
def timecode_to_frames (s, fps):
    d = s.split(':')
    mult = fps
    frames = float(d.pop(-1))
    while len (d):
        frames = frames + float(d.pop(-1))*mult
        mult = mult * 60.0
    return round(frames)
    
#def frames_to_frames (frames, fps):
#    return timecode_to_frames(frames_to_timecode(frames, fps),fps)
#    
#def test (max, fps):
#    for f in range(max):
#        if f != frames_to_frames(f, fps):
#            print (f)
#            break

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
    currentClipInfo = None
    sliderMask = 0
    clipListDict = {}
    clipList = []

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        self.parent = parent
        
        # Init the kipro stuff
        host = Settings.Config.get("KiPro","ip")
        if len(host):
            try:
                self.kipro = kipro.Client("http://" + host)
            except:
                self.kipro = None
            
        self.timecodeUpdateThread = None
        if self.kipro:
            self.timecodeUpdateThread = TimecodeUpdater("http://" + host, self, self.TimecodeCallback, self.OnEndClip)
            self.timecodeUpdateThread.start()
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        if self.kipro:
            self.infoBar = wx.StaticText(self, -1, "KiPro: Connected to KiPro")
        else:
            self.infoBar = wx.StaticText(self, -1, "KiPro: Kipro Offline")
        panelSizer.Add(self.infoBar)
        
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
        self.currentTimeText = wx.TextCtrl (self, style = wx.TE_READONLY, value = frames_to_timecode(0,30))
        sizer.Add(self.currentTimeText, flag=wx.EXPAND)
        #panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        #sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Current State"))
        self.currentStateText = wx.TextCtrl (self, style = wx.TE_READONLY)
        sizer.Add(self.currentStateText, flag=wx.EXPAND)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        # Time Slider
        self.timeslider = wx.Slider(self, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        panelSizer.Add(self.timeslider, border = 5, flag=wx.EXPAND|wx.ALL)
        self.Bind(wx.EVT_SLIDER, self.OnSetTime, self.timeslider)
        
        # Duration Labels
        self.timeElapsed = wx.StaticText(self)
        self.timeRemaining = wx.StaticText(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.timeElapsed, border = 5, flag=wx.LEFT)
        sizer.AddStretchSpacer()
        sizer.Add(self.timeRemaining, border = 5, flag=wx.RIGHT)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.BOTTOM)
        
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
        self.SetSizer(panelSizer)
        self.Layout()
        #wx.lib.scrolledpanel.ScrolledPanel.SetupScrolling(self)
        
        # Start a timer to get latest setting from kipro
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2e+3) # 2 second interval
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
    
    def OnCueClip (self, evt=None):
        if self.kipro:
            self.kipro.cueToTimecode(self.startTimeText.GetValue())
            
    def OnShowClip (self, evt):
        self.ShowingClip = True
        self.timeslider.Disable()
        self.startTimeText.Disable()
        self.stopTimeText.Disable()
        # Prep clip
        self.OnCueClip()
        time.sleep(0.2)
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(self.stopTimeText.GetValue())
            
        if self.parent.panelHS50.MainDisplayed:
            # Prep Video Switcher.  Set Preview to the correct channel
            self.parent.panelHS50.panelMain.ChangeOutput('PVW', Settings.Config.get("HS50","KiProChannel"))
        
            # Video Switcher PGM Fade-to-Black
            self.parent.panelHS50.panelMain.OnFTB()
            
            # Wait for fade to complete
            time.sleep(1)
            
            # Video Switcher: Get and store AUX channel
            self.SavedAuxChannel = self.parent.panelHS50.panelMain.AUX_radio.GetSelection() # Returns number
            self.SavedAuxChannel = self.parent.panelHS50.panelMain.AUX_radio.GetItemLabel(self.SavedAuxChannel) # Returns label
            
            # Video Switcher: AUX to PGM
            self.parent.panelHS50.panelMain.ChangeOutput('AUX', 'PGM')
                
        # TODO: Audio Mixer: Fade Out
            
        # Start clip
        if self.kipro:
            self.kipro.play()
            
        if self.parent.panelHS50.MainDisplayed:
            # Video Switcher: Swap PGM/PVW and Un-Fade-to-Black
            self.parent.panelHS50.panelMain.OnCut()
            self.parent.panelHS50.panelMain.OnFTB()
        
        # TODO: Audio Mixer: Fade In
        
        if self.parent.panelProjectors.MainDisplayed:
            # Side Projectors: Un-shutter
            self.parent.panelProjectors.panelMain.SetShutter(False)
            
    def OnEndClip (self, evt=None):
    
        if self.ShowingClip:
            if self.parent.panelHS50.MainDisplayed:
                # Video Switcher: Fade-to-black
                self.parent.panelHS50.panelMain.OnFTB()
            
            # TODO: Audio Mixer: Fade Out
            
            # Wait for fade to complete.  Cut it a little short
            time.sleep(0.75)
            
        # Stop playback
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(None)
        if self.kipro:
            self.kipro.stop()
            
        if self.ShowingClip:
            if self.parent.panelProjectors.MainDisplayed:
                # Side Projectors: Shutter
                self.parent.panelProjectors.panelMain.SetShutter(True)

            if self.parent.panelHS50.MainDisplayed:
                # Video Switcher: Restore AUX
                self.parent.panelHS50.panelMain.ChangeOutput('AUX', self.SavedAuxChannel)
                
                # Video Switcher: Swap PGM/PVW and Un-Fade-to-Black
                self.parent.panelHS50.panelMain.OnCut()
                self.parent.panelHS50.panelMain.OnFTB()
            
        self.ShowingClip = False
        self.timeslider.Enable()
        self.startTimeText.Enable()
        self.stopTimeText.Enable()
            
    def OnSelectClipButton (self, evt):
        if self.kipro:
            self.kipro.goToClip(self.clipList[self.playListCombobox.GetSelection()])

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
        time.sleep(0.1)
        if self.kipro:
            self.kipro.play()
            
    def OnPlayTo (self, evt):
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(self.stopTimeText.GetValue())
        if self.kipro:
            # Cue to approx. 5 seconds before end time.  
            self.kipro.cueToTimecode(frames_to_timecode(timecode_to_frames(self.stopTimeText.GetValue(), 30) - 5*30, 30))
            time.sleep(0.2)
            self.kipro.play()
            
    def LongClipName (self, clipName):
        try:
            return "%-25s%-30s%s" % (clipName, 
                                    self.clipListDict[clipName]['timestamp'], 
                                    self.clipListDict[clipName]['duration'])
        except:
            return clipName

    def OnTimer (self, evt):
        if self.kipro:
            # Get the clip list
            self.clipListDict = self.kipro.getClipList()
            clipList = list(self.clipListDict.keys())

            if self.clipList != clipList:
                self.clipList = clipList
                self.playListCombobox.SetItems([self.LongClipName(clip) for clip in clipList])

            # Get the current clip name
            currentClipName = self.kipro.getCurrentClipName()
            self.currentClipText.SetValue(self.LongClipName(currentClipName))
            
            # Store clip data
            self.currentClipInfo = None
            try:
                self.currentClipInfo = self.clipListDict[currentClipName]
            except:
                pass
                
            # Get the current transport state
            self.currentStateText.SetValue(self.kipro.getTransporterState()[1])
            
    def OnFillStartTime (self, evt):
        self.startTimeText.SetValue(self.currentTimeText.GetValue())
            
    def OnFillStopTime (self, evt):
        self.stopTimeText.SetValue(self.currentTimeText.GetValue())
        
    def TimecodeCallback (self, timecode):
        self.currentTimeText.SetValue(timecode)        
        fps = float(self.currentClipInfo["framerate"])
        timecode_frames = timecode_to_frames(timecode, fps)
        if self.ShowingClip:
            # Times are from the selected part of the clip
            starting_frames = timecode_to_frames(self.startTimeText.GetValue(), fps)
            duration_frames = timecode_to_frames(self.stopTimeText.GetValue(), fps) - timecode_to_frames(self.startTimeText.GetValue(), fps)
        else:
            # Times are from the full clip
            starting_frames = timecode_to_frames(self.currentClipInfo["attributes"]["Starting TC"], fps)
            duration_frames = int(self.currentClipInfo["framecount"])
            if timecode_frames == 0:
                # Transport must be stopped
                timecode_frames = starting_frames           
        
        # See if we can move the slider
        if self.sliderMask:
            self.sliderMask -= 1
        else:
            # Update the Time Slider
            # Position = MaxValue * (currentFrames - startFrames) / duration
            if self.currentClipInfo:
                percent = (timecode_frames - starting_frames) / duration_frames
                self.timeslider.SetValue(percent * self.timeslider.GetMax()) 
        
        # Update Elapsed Time
        elapsed_time_frames = timecode_frames - starting_frames
        self.timeElapsed.SetLabel(frames_to_timecode(elapsed_time_frames, fps, True))
        
        # Update Time Remaining 
        self.timeRemaining.SetLabel(frames_to_timecode(duration_frames - elapsed_time_frames, fps, True))
        
        #self.Sizer.Layout()
        
    def OnSetTime(self, evt):
        # CueTimecode = StartTimecode + (position/MaxValue) * durationTimecode
        if self.currentClipInfo:
            fps = float(self.currentClipInfo["framerate"])
            slideRatio = self.timeslider.GetValue() / self.timeslider.GetMax()
            slideFrame = timecode_to_frames(self.currentClipInfo["attributes"]["Starting TC"], fps) + \
                        slideRatio * int(self.currentClipInfo["framecount"])
            if self.kipro:
                transportState = self.kipro.getTransporterState()[1] # Transport is paused in cueToTimecode
                self.kipro.cueToTimecode(frames_to_timecode(slideFrame, fps))
                self.sliderMask = 2 # Wait two updates before moving slider

    def OnDestroy (self, evt):
        # Cleanup Timer
        self.timer.Stop()
        
        # Cleanup Thread
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.stop()
            self.timecodeUpdateThread.join()
        
        # Let the event pass
        evt.Skip()
        
