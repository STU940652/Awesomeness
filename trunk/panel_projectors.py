import wx
import wx.lib.scrolledpanel 
import pjlink
import traceback
import Settings
import collections

class PanelProjector (wx.Panel):

    projectors = []

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(wx.StaticText(self, -1, "Projectors"))
        sizer = wx.FlexGridSizer(cols = 3, vgap = 5, hgap = 5)
        
        self.groups = collections.defaultdict(lambda: list())
        
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
                #traceback.print_exc()
                
            # Built the UI
            name = Settings.Config.get("projector", "name%i" % i, fallback=str(i))
            group = Settings.Config.get("projector", "group%i" % i, fallback="sides")
            sizer.Add(wx.StaticText(self, -1, name))
            
            onoffText = wx.TextCtrl (self, -1, "offline", style=wx.TE_READONLY)
            sizer.Add(onoffText)
            
            shutterCheck = wx.CheckBox(self, -1, label = "Shuttered")
            self.Bind(wx.EVT_CHECKBOX, self.OnShutter, shutterCheck)
            sizer.Add(shutterCheck)
                
            self.projectors.append( (proj, onoffText, shutterCheck) )
            if group:
                self.groups[group].append( (proj, onoffText, shutterCheck) )
            

        
        panelSizer.Add(sizer, border = 5, proportion=0, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from HS50
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1e+3) # 1 second interval

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
    def SetShutter (self, shutter, group = "sides"):
        proj_list = self.projectors
        
        if group and group in self.groups:
            proj_list = self.groups[group]
            
        for proj, onoffText, shutterCheck in self.projectors:
            if proj:
                proj.set_mute(pjlink.MUTE_VIDEO | pjlink.MUTE_AUDIO, shutter)
                
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

    def OnDestroy (self, evt):
        # Cleanup Timer
        self.timer.Stop()
        
        # Let the event pass
        evt.Skip()
        
                