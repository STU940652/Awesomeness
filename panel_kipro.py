import wx
import wx.lib.scrolledpanel 
import time
import configparser
import threading
import Settings
import os
import os.path
import collections
import logging

from AJArest import kipro

presetFileName = 'KiPro_presets.ini'

# Time conversion helper
def frames_to_timecode (frames, fps, hms_only = False):
    frames = float(frames)
    h = int(frames/(60*60*fps))
    msl = frames - h*60*60*fps
    m = int(msl/(60*fps))
    msl = msl - m*60*fps
    s = int(msl/fps)
    f = round(msl-s*fps)
    if h > 24: h -= 24
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
        self.SetToolTip(data.replace("Command","").strip())
        
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
    currentClipInfo = None
    sliderMask = 0
    clipListDict = {}
    clipList = []
    StaleState = True
    SideProjectorsKumoSource = None
    SideProjectorsInputSource = None
    SideProjectorsShutters = None

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
        self.presetListCombobox = wx.ComboBox(self, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.UpdatePresetList, self.presetListCombobox)
        sizer.Add(self.presetListCombobox, proportion = 1, flag=wx.EXPAND)
        self.presetLoadButton = wx.Button (self, -1, "Load Preset")
        self.Bind(wx.EVT_BUTTON, self.LoadPreset, self.presetLoadButton)
        sizer.Add(self.presetLoadButton)
        self.presetSaveButton = wx.Button (self, -1, "Save Preset")
        self.Bind(wx.EVT_BUTTON, self.SavePreset, self.presetSaveButton)
        sizer.Add(self.presetSaveButton)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        self.UpdatePresetList()
        
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
                    ("O",   "Record Command"),
                    (">|",  "Single Step Forward"),
                    (">",   "Play Command"),
                    (">>",  "Fast Forward") )
        for buttonLable, buttonCommand in buttons:
            button = ButtonWithData(self, -1, buttonLable, size = (30,-1))
            if (buttonCommand ==  "Record Command"):
                button.SetForegroundColour(wx.RED)
            button.SetData(buttonCommand)
            self.Bind(wx.EVT_BUTTON, self.OnTransportButton, button)
            sizer.Add(button)
        sizer.AddStretchSpacer(1)
        self.StopLock = wx.CheckBox(self, -1, label = "Stop Lock")
        self.StopLock.SetValue(True)
        sizer.Add(self.StopLock)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        sizer_v = wx.BoxSizer(wx.VERTICAL)
        
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
        sizer_v.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
                
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cueClipButton = wx.Button (self, -1, "Cue Clip")
        self.Bind(wx.EVT_BUTTON, self.OnCueClip, self.cueClipButton)
        sizer.Add(self.cueClipButton)
        self.showClipButton = wx.Button (self, -1, "Show Clip")
        self.showClipButton.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnShowClip, self.showClipButton)
        sizer.Add(self.showClipButton)
        self.cancelClipButton = wx.Button (self, -1, "Cancel Clip")
        self.Bind(wx.EVT_BUTTON, self.OnEndClip, self.cancelClipButton)
        sizer.Add(self.cancelClipButton)
        sizer.AddStretchSpacer(1)
        sizer_v.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        sizer_h.Add(sizer_v, flag=wx.EXPAND)

        sizer_h.AddStretchSpacer(1)

        panelSizer.Add(sizer_h, border = 5, flag=wx.EXPAND|wx.ALL)
        
        panelSizer.AddStretchSpacer()
        self.SetSizer(panelSizer)
        self.Layout()
        #wx.lib.scrolledpanel.ScrolledPanel.SetupScrolling(self)
        
        # Start a timer to get latest setting from kipro
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2e+3) # 2 second interval
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
        # Test
        if False:
            if self.parent.panelProjectors.MainDisplayed:
                old = self.parent.panelProjectors.panelMain.GetInput("sides")
                self.parent.panelProjectors.panelMain.SetInput("DIGITAL 1", "sides")
                time.sleep(5)
                self.parent.panelProjectors.panelMain.SetInput(old, "sides")
        
    def UpdatePresetList (self, evt=None):
        # Get preset settings if they exist
        Presets=configparser.SafeConfigParser(delimiters = ('='))
        Presets.optionxform = lambda option: option
        Presets.read([os.path.join(d, presetFileName) for d in Settings.data_directory_list])
        
        if "KiProPresets" in Presets:
            presetNames = list(Presets["KiProPresets"])
        else:
            presetNames = []
            
        self.presetListCombobox.Set([n.strip("'") for n in presetNames])
     
    def SavePreset (self, evt):
        thisPreset = "'%30s ~ %15s ~ %15s'" % (
                        self.playListCombobox.GetValue(),
                        self.startTimeText.GetValue(),
                        self.stopTimeText.GetValue()
                        )
                        
        # Get preset settings if they exist
        Presets=configparser.SafeConfigParser(delimiters = ('='))
        Presets.optionxform = lambda option: option
        Presets.read([os.path.join(d, presetFileName) for d in Settings.data_directory_list])
        
        if "KiProPresets" in Presets:
            presetNames = list(Presets["KiProPresets"])
        else:
            presetNames = []
        presetNames.insert(0, thisPreset)
        presetNames = presetNames[:10]
        
        Presets["KiProPresets"]=collections.OrderedDict( (p, "") for  p in presetNames) # {p: '' for p in presetNames}

        for data_directory in Settings.data_directory_list[1:]:
            try:
                with open(os.path.join(data_directory,presetFileName), 'w') as configfile:
                    Presets.write(configfile)
            except:
                traceback.print_exc()  
                
        self.presetListCombobox.Set([n.strip("'") for n in presetNames])
        self.presetListCombobox.SetValue(thisPreset.strip("'"))
        
    def LoadPreset (self, evt):
        # If we are playing, don't mess with anything
        if "play" in self.currentStateText.GetValue().lower():
            return
    
        preset = self.presetListCombobox.GetValue()
        try:
            clip_name, start, stop = preset.split(' ~ ')
        except ValueError:
            return
        
        self.playListCombobox.SetValue(clip_name.strip())
        if self.playListCombobox.GetValue() == clip_name.strip():
            self.OnSelectClipButton()
        self.startTimeText.SetValue(start.strip())
        self.stopTimeText.SetValue(stop.strip())
        
    def OnCueClip (self, evt=None):
        logging.info("KiPro OnCueClip: %s", str(evt))
        if evt: self.showClipButton.Enable(True)
        if self.kipro:
            self.kipro.cueToTimecode(self.startTimeText.GetValue())
             
    def OnShowClip (self, evt):
        logging.info("KiPro OnShowClip: %s", str(evt))
        self.showClipButton.Enable(False)
        self.ShowingClip = True
        self.timeslider.Disable()
        self.startTimeText.Disable()
        self.stopTimeText.Disable()
        # Prep clip
        self.OnCueClip()
        time.sleep(0.2)
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(self.stopTimeText.GetValue())
                    
        if self.parent.panelATEM.MainDisplayed:
            # Video Switcher Start Macro
            self.parent.panelATEM.panelMain.OnStart()
        
        if self.kipro:
            # Start clip
            self.kipro.play()
                        
    def OnEndClip (self, evt=None):
        """
        This is the 3-screen version of End Clip
        """
        logging.info("KiPro OnEndClip: %s", str(evt))
        if self.ShowingClip:
            if self.parent.panelATEM.MainDisplayed:
                # Video Switcher End Macro
                self.parent.panelATEM.panelMain.OnEnd()
            
            # Wait for fade to complete.  Cut it a little short
            time.sleep(0.5)
                
        # Stop playback
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(None)
        if self.kipro:
            # See if we should block the command
            if self.StopLock.GetValue():
                if self.StaleState:
                    # Update Transport State if there is a command in flight
                    self.OnTimer(None)
                if self.currentStateText.GetValue() != "Paused":
                    # Transport is not paused.  Ok to stop
                    self.kipro.stop()
            
        self.ShowingClip = False
        self.timeslider.Enable()
        self.startTimeText.Enable()
        self.stopTimeText.Enable()
            
    def OnSelectClipButton (self, evt=None):
        if self.kipro:
            self.kipro.goToClip(self.clipList[self.playListCombobox.GetSelection()])

    def OnTransportButton (self, evt=None):
        command = evt.GetEventObject().GetData()
        
        # See if we should block the command
        if (command == "Stop Command") and (self.StopLock.GetValue()):
            if self.StaleState:
                # Update Transport State if there is a command in flight
                self.OnTimer(None)
            if self.currentStateText.GetValue() == "Paused":
                # Transport is paused.  Block the stop
                return            
        
        if self.kipro:
            self.kipro.sendTransportCommandByDescription(command)
            self.StaleState = True
            
        if self.timecodeUpdateThread:
            self.timecodeUpdateThread.setStopTime(None)
            
    def OnCueStart (self, evt=None):
        logging.info("KiPro OnCueStart: %s", str(evt))
        if self.kipro:
            self.kipro.cueToTimecode(self.startTimeText.GetValue())

    def OnPlayFrom (self, evt):
        logging.info("KiPro OnPlayFrom: %s", str(evt))
        self.OnCueStart()
        time.sleep(0.1)
        if self.kipro:
            self.kipro.play()
            
    def OnPlayTo (self, evt):
        logging.info("KiPro OnPlayTo: %s", str(evt))
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
            self.StaleState = False
            
    def OnFillStartTime (self, evt):
        self.startTimeText.SetValue(self.currentTimeText.GetValue())
            
    def OnFillStopTime (self, evt):
        self.stopTimeText.SetValue(self.currentTimeText.GetValue())
        
    def TimecodeCallback (self, timecode):
        self.currentTimeText.SetValue(timecode)
        if self.currentClipInfo:    
            fps = float(self.currentClipInfo["framerate"])
        else:
            fps = 29.95
        timecode_frames = timecode_to_frames(timecode, fps)
        if self.ShowingClip:
            # Times are from the selected part of the clip
            starting_frames = timecode_to_frames(self.startTimeText.GetValue(), fps)
            duration_frames = timecode_to_frames(self.stopTimeText.GetValue(), fps) - timecode_to_frames(self.startTimeText.GetValue(), fps)
        else:
            # Times are from the full clip
            if self.currentClipInfo:
                starting_frames = timecode_to_frames(self.currentClipInfo["attributes"]["Starting TC"], fps)
                duration_frames = int(self.currentClipInfo["framecount"])
            else:
                starting_frames = 0
                duration_frames = 1
            if timecode_frames == 0:
                # Transport must be stopped
                timecode_frames = starting_frames           
        
        if (timecode_frames - starting_frames) < 0:
            timecode_frames += timecode_to_frames("24:00:00:00", fps)
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
        if (duration_frames == 0):
            self.timeRemaining.SetLabel('')
        else:
            self.timeRemaining.SetLabel(frames_to_timecode(duration_frames - elapsed_time_frames, fps, True))
        
        #self.Sizer.Layout()
        
    def OnSetTime(self, evt):
        # CueTimecode = StartTimecode + (position/MaxValue) * durationTimecode
        if self.currentClipInfo:
            fps = float(self.currentClipInfo["framerate"])
            slideRatio = self.timeslider.GetValue() / self.timeslider.GetMax()
            slideFrame = timecode_to_frames(self.currentClipInfo["attributes"]["Starting TC"], fps) + \
                        slideRatio * int(self.currentClipInfo["framecount"])
            # Some debug info
            # print ( fps, 
            #         slideRatio, 
            #         slideFrame, 
            #         timecode_to_frames(self.currentClipInfo["attributes"]["Starting TC"], fps), 
            #         int(self.currentClipInfo["framecount"]), 
            #         frames_to_timecode(slideFrame, fps))
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
        
