import wx
import socket
import traceback

HOST = '10.70.58.14'    # The remote host
PORT = 60040            # Standard prot for HS50

STX = b'\x02'
ETX = b'\x03'


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
        
        # Init the connection
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, PORT))
            self.online=True
        except:
            traceback.print_exc()
            self.online=False
            
        if self.online:
            self.infoBar.ShowMessage("Connected to HS50")
        else:
            self.infoBar.ShowMessage("HS50 Offline")
                    
        panelSizer = wx.BoxSizer(wx.VERTICAL)
                
        # Program Output
        self.AUX_radio = wx.RadioBox(self,label = "AUX: Auxilliary", choices = ["1","2","3","4","5","FMEM1","FMEM2","PGM"])
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeOutput, self.AUX_radio)
        panelSizer.Add(self.AUX_radio, border = 5, flag=wx.EXPAND|wx.ALL)       
        
        self.PGM_radio = wx.RadioBox(self,label = "PGM: Program", choices = ["1","2","3","4","5","FMEM1","FMEM2"])
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeOutput, self.PGM_radio)
        panelSizer.Add(self.PGM_radio, border = 5, flag=wx.EXPAND|wx.ALL)

        self.PVW_radio = wx.RadioBox(self,label = "PVW: Preview", choices = ["1","2","3","4","5","FMEM1","FMEM2"])
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeOutput, self.PVW_radio)
        panelSizer.Add(self.PVW_radio, border = 5, flag=wx.EXPAND|wx.ALL)

        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddStretchSpacer(1)
        self.cutButton = wx.Button (self, -1, "Cut")
        #self.Bind(wx.EVT_BUTTON, self.OnFillStartTime, self.startTimeFillButton)
        sizer.Add(self.cutButton)
        sizer.AddStretchSpacer(1)
        self.fadeButton = wx.Button (self, -1, "Auto Fade")
        #self.Bind(wx.EVT_BUTTON, self.OnFillStartTime, self.startTimeFillButton)
        sizer.Add(self.fadeButton)
        sizer.AddStretchSpacer(1)
        self.ftbButton = wx.Button (self, -1, "Fade to Black")
        #self.Bind(wx.EVT_BUTTON, self.OnFillStartTime, self.startTimeFillButton)
        sizer.Add(self.ftbButton)
        sizer.AddStretchSpacer(1)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND)
        
        panelSizer.AddStretchSpacer()
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from HS50
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        #self.timer.Start(2e+3) # 2 second interval

    def OnChangeOutput (self, evt):
        if evt.GetEventObject() == self.AUX_radio:
            bus = b"12"
        elif evt.GetEventObject() == self.PGM_radio:
            bus = b"02"
        elif evt.GetEventObject() == self.PVW_radio:
            bus = b"03"
        else:
            return
            
        inputList=[b"50", b"51", b"52", b"53", b"54", b"73", b"74", b"77"]
        
        c = STX + b"SBUS:" + bus + b":" + inputList[evt.GetEventObject().GetSelection()] + ETX
        self.socket.sendall(c)
        #print (c)
    
