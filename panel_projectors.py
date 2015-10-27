import wx
import wx.lib.scrolledpanel 
import pjlink
import traceback
import Settings

class PanelProjector (wx.lib.scrolledpanel.ScrolledPanel):

    projectors = []

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        self.infoBar = wx.InfoBar(self)
        
        # Init the connection
        for i in range(5):
            host = Settings.Config.get("projector","ip%i" % i, None)
            port = 4352
            password = 'panasonic' # default password
            if host == None:
                break
            try:
                sock = socket()
                sock.connect((host, port))
                f = sock.makefile()

                get_password = lambda: password
                proj = Projector(f)
                rv = proj.authenticate(get_password)
                if rv is False:
                    print('Incorrect password.', file=sys.stderr)
                projectors.append(proj)
            except:
                traceback.print_exc()

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        for thisProjector in projectors:
            pass
        
        
        
                
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
        #wx.lib.scrolledpanel.ScrolledPanel.SetupScrolling(self)
        
        # Start a timer to get latest setting from HS50
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(0.2e+3) # 0.2 second interval

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
        pass