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
        wx.Panel.__init__(self, parent, -1)

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
        #self.PresetSelection = wx.ComboBox(self)
        #panelSizer.Add(self.PresetSelection, flag=wx.EXPAND)
        #self.UpdatePresetList()
        
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
        
        panelSizer.Add(sizer, flag = wx.EXPAND)
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
