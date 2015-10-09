import wx
import configparser
from AJArest import kipro

class ButtonWithData (wx.Button):
    Data = None
    
    def SetData (self, data):
        self.Data = data
        
    def GetData (self):
        return self.Data

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
            
        if self.kipro:
            print (self.kipro.getPlaylists())
            print (self.kipro.getCurrentClipName())
            # goToClip(self, clipName)
            # cueToTimecode(self, timecode)
            # l = kipro.TimecodeListener("http://10.70.58.26")
            # l.start()
            # print l.getTimecode()
            
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.playListCombobox = wx.ComboBox(self, style = wx.CB_READONLY|wx.CB_DROPDOWN,)
        sizer.Add(self.playListCombobox, proportion = 1, flag=wx.EXPAND)
        self.cuePlaylistButton = wx.Button (self, -1, "Select")
        sizer.Add(self.cuePlaylistButton)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Current Clip"))
        self.currentClipText = wx.TextCtrl (self, style = wx.TE_READONLY)
        sizer.Add(self.currentClipText, proportion = 1, flag=wx.EXPAND)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Current Time"))
        self.currentTimeText = wx.TextCtrl (self, style = wx.TE_READONLY)
        sizer.Add(self.currentTimeText, flag=wx.EXPAND)
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
        sizer.Add(self.startTimeFillButton)
        self.startTimeCueButton = wx.Button (self, -1, "Cue")
        sizer.Add(self.startTimeCueButton)
        self.startTimePlayFromButton = wx.Button (self, -1, "Play From")
        sizer.Add(self.startTimePlayFromButton)
        
        sizer.Add(wx.StaticText(self, -1, "Stop Time"))
        self.stopTimeText = wx.TextCtrl (self, value = "00:00:00.000")
        sizer.Add(self.stopTimeText, proportion = 1, flag=wx.EXPAND)
        self.stopTimeFillButton = wx.Button (self, -1, "Fill")
        sizer.Add(self.stopTimeFillButton)
        #self.stopTimeCueButton = wx.Button (self, -1, "Cue")
        sizer.AddStretchSpacer()
        self.stopTimePlayToButton = wx.Button (self, -1, "Play To")
        sizer.Add(self.stopTimePlayToButton)        
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
                
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.showClipButton = wx.Button (self, -1, "Show Clip")
        sizer.Add(self.showClipButton)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        panelSizer.AddStretchSpacer()
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from kipro
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        #self.timer.Start(2e+3) # 2 second interval
    
    def OnTransportButton (self, evt):
        command = evt.GetEventObject().GetData()
        if self.kipro:
            self.kipro.sendTransportCommandByDescription(command)
            
    def UpdatePlaylist (self):
        playlist = []
        if self.kipro: 
            playlist = self.kipro.getPlaylists()
            
        self.playListCombobox.SetItems(playlist)
    
    def OnCueButton (self, evt):
        if self.kipro:
            self.kipro.goToClip(self.playListCombobox.GetValue())
