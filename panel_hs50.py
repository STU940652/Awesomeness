import wx

class ButtonWithData (wx.Button):
    Data = None
    
    def SetData (self, data):
        self.Data = data
        
    def GetData (self):
        return self.Data

class PanelHS50 (wx.Panel):

    online = False

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        self.infoBar = wx.InfoBar(self)
        
        # Init the kipro stuff
        #try:
        #    self.kipro = kipro.Client("http://10.70.58.26")
        #except:
            
        if self.online:
            self.infoBar.ShowMessage("Connected to HS50")
        else:
            self.infoBar.ShowMessage("HS50 Offline")
                    
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        
        # Program Output
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons = ( ("1",  "Fast Reverse"),
                    ("2",   "Play Reverse Command"),
                    ("3",  "Single Step Reverse"),
                    ("4",   "Stop Command"),
                    ("5",  "Single Step Forward"))
        for buttonLable, buttonCommand in buttons:
            button = ButtonWithData(self, -1, buttonLable)
            button.SetData(buttonCommand)
            #self.Bind(wx.EVT_BUTTON, self.OnTransportButton, button)
            sizer.Add(button)        
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        
        #sizer = wx.FlexGridSizer(cols = 5)
        #sizer.Add(wx.StaticText(self, -1, "Start Time"))
        #self.startTimeText = wx.TextCtrl (self, value = "00:00:00.000")
        #sizer.Add(self.startTimeText, proportion = 1, flag=wx.EXPAND)
        #self.startTimeFillButton = wx.Button (self, -1, "Fill")
        #self.Bind(wx.EVT_BUTTON, self.OnFillStartTime, self.startTimeFillButton)
        #sizer.Add(self.startTimeFillButton)
        #self.startTimeCueButton = wx.Button (self, -1, "Cue")
        #self.Bind(wx.EVT_BUTTON, self.OnCueStart, self.startTimeCueButton)
        #sizer.Add(self.startTimeCueButton)
        #self.startTimePlayFromButton = wx.Button (self, -1, "Play From")
        #self.Bind(wx.EVT_BUTTON, self.OnPlayFrom, self.startTimePlayFromButton)
        #sizer.Add(self.startTimePlayFromButton)
        #panelSizer.Add(sizer, border = 5, flag=wx.EXPAND|wx.ALL)
        
        panelSizer.AddStretchSpacer()
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from kipro
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        #self.timer.Start(2e+3) # 2 second interval
