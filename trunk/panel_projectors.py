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
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.FlexGridSizer(cols = 3)
        
        # Init the connection
        for i in range(1, 5):
            host = Settings.Config.get("projector","ip%i" % i, fallback=None)
            get_password = lambda: 'panasonic' # default password
            
            if host == None:
                break
            try:
                proj = pjlink.Projector(host)
                rv = proj.authenticate(get_password)
                if rv is False:
                    print('Incorrect password.', file=sys.stderr)
                    
            except:
                proj = None
                traceback.print_exc()
                
            # Built the UI
            name = Settings.Config.get("projector", "name%i" % i, fallback=str(i))
            sizer.Add(wx.StaticText(self, -1, name))
            
            onoffText = wx.TextCtrl (self, -1, "offline", style=wx.TE_READONLY)
            sizer.Add(onoffText)
            
            shutterCheck = wx.CheckBox(self, -1, label = "Shuttered")
            self.Bind(wx.EVT_CHECKBOX, self.OnShutter, shutterCheck)
            sizer.Add(shutterCheck)
                
            self.projectors.append( (proj, onoffText, shutterCheck) )

        
        panelSizer.Add(sizer, border = 5, proportion=1, flag=wx.EXPAND|wx.CENTER)
        
        panelSizer.AddStretchSpacer()
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from HS50
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(0.2e+3) # 0.2 second interval

    def OnShutter (self, evt):
        for proj, onoffText, shutterCheck in self.projectors:
            if proj and (shutterCheck == evt.GetEventObject()):
                proj.set_mute(pjlink.MUTE_VIDEO | pjlink.MUTE_AUDIO, shutterCheck.GetValue())
        
    def OnTimer (self, evt):
        for proj, onoffText, shutterCheck in self.projectors:
            if proj:
                onoffText.SetValue(proj.get_power())
                a, v = proj.get_mute()
                shutterCheck.SetValue(a)
            