import wx
import socket
import traceback
import re
import collections
import Settings

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
    socket = None
    inputList=[b"50", b"51", b"52", b"53", b"54", b"73", b"74", b"77"]

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        self.infoBar = wx.InfoBar(self)
        
        #Some variables
        self.requestList=collections.deque([b"12", b"02", b"03"])
        
        # Init the connection
        host = Settings.Config.get("HS50","ip")
        if len(host):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((host, PORT))
                self.socket.setblocking(False)
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
        self.Bind(wx.EVT_BUTTON, self.OnCut, self.cutButton)
        sizer.Add(self.cutButton)
        sizer.AddStretchSpacer(1)
        self.fadeButton = wx.Button (self, -1, "Auto Fade")
        self.Bind(wx.EVT_BUTTON, self.OnFade, self.fadeButton)
        sizer.Add(self.fadeButton)
        sizer.AddStretchSpacer(1)
        self.ftbButton = wx.Button (self, -1, "Fade to Black")
        self.Bind(wx.EVT_BUTTON, self.OnFTB, self.ftbButton)
        sizer.Add(self.ftbButton)
        sizer.AddStretchSpacer(1)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND)
        
        panelSizer.AddStretchSpacer()
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from HS50
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(0.2e+3) # 0.2 second interval

    def OnCut (self, evt):
        c = STX + b"SCUT:00" + ETX
        if self.socket:
            self.socket.sendall(c)
        
    def OnFade (self, evt):
        c = STX + b"SAUT:00:0" + ETX
        if self.socket:
            self.socket.sendall(c)
        
    def OnFTB (self, evt):
        c = STX + b"SAUT:06:0" + ETX
        if self.socket:
            self.socket.sendall(c)
        
    def OnChangeOutput (self, evt):
        if evt.GetEventObject() == self.AUX_radio:
            bus = b"12"
        elif evt.GetEventObject() == self.PGM_radio:
            bus = b"02"
        elif evt.GetEventObject() == self.PVW_radio:
            bus = b"03"
        else:
            return
                    
        c = STX + b"SBUS:" + bus + b":" + self.inputList[evt.GetEventObject().GetSelection()] + ETX
        if self.socket:
            self.socket.sendall(c)
        #print (c)
        
    def OnTimer (self, evt):
        self.message = b''
        try:
            if self.socket:
                self.message = self.socket.recv(200)
        except:
            pass
            
        # See if there are any incoming messages
        if len(self.message):
            print (self.message)
            # Find the message of interest.  Discard anything before it.  Preserve everything after it
            r = re.search(STX + "ABSC:([0-9]{2}):([0-9]{2}):([0-9]{1})" + ETX + "(.*)", self.message)
            if r:
                bus, material, tally, self.message = r.groups()
                
                # Which radio button do we need to update?
                bus_radio = None
                if bus == b"12":
                    bus_radio = self.AUX_radio
                elif bus == b"02":
                    bus_radio = self.PGM_radio
                elif bus == b"03":
                    bus_radio = self.PVW_radio
                
                # Set the radio button
                if bus_radio and (material in self.inputList):
                    bus_radio.SetSelection(self.inputList.index(material))
                    
        # Send the next request
        self.requestList.rotate()
        c = STX + b"QBSC:" + self.requestList[0] + ETX
        try:
            if self.socket:
                self.socket.sendall(c)
        except:
            pass
        