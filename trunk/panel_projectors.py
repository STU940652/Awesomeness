import wx
import wx.lib.scrolledpanel 
import pjlink
import traceback
import Settings
import collections

class PanelProjector (wx.lib.scrolledpanel.ScrolledPanel):

    projectors = []

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(wx.StaticText(self, -1, "Projectors"))
        sizer = wx.FlexGridSizer(cols = 5, vgap = 5, hgap = 5)
        
        self.groups = collections.defaultdict(lambda: list())
        
        # Init the connection
        for i in range(1, 15):
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
            
            on_button = wx.Button (self, -1, "On")
            self.Bind(wx.EVT_BUTTON, self.OnDisplayOnButton, on_button)
            sizer.Add(on_button)
                
            off_button = wx.Button (self, -1, "Off")
            self.Bind(wx.EVT_BUTTON, self.OnDisplayOffButton, off_button)
            sizer.Add(off_button)
                
            self.projectors.append( (proj, onoffText, shutterCheck, on_button, off_button) )
            if group:
                self.groups[group].append( (proj, onoffText, shutterCheck, on_button, off_button) )
            

        
        panelSizer.Add(sizer, border = 5, proportion=0, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from HS50
        self.OnTimer(None)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(10e+3) # 10 second interval

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
    def SetShutter (self, shutter, group = "sides"):
        proj_list = self.projectors
        
        if group and group in self.groups:
            proj_list = self.groups[group]
            
        for proj, onoffText, shutterCheck, on_button, off_button in proj_list:
            if proj:
                proj.set_mute(pjlink.MUTE_VIDEO | pjlink.MUTE_AUDIO, shutter)
                
    def OnShutter (self, evt):
        for proj, onoffText, shutterCheck, on_button, off_button in self.projectors:
            if proj and (shutterCheck == evt.GetEventObject()):
                proj.set_mute(pjlink.MUTE_VIDEO | pjlink.MUTE_AUDIO, shutterCheck.GetValue())
        
    def OnDisplayOnButton (self, evt):
        for proj, onoffText, shutterCheck, on_button, off_button in self.projectors:
            if proj and (on_button == evt.GetEventObject()):
                proj.set_power("on")
        self.OnTimer(None)
        
    def OnDisplayOffButton (self, evt):
        for proj, onoffText, shutterCheck, on_button, off_button in self.projectors:
            if proj and (off_button == evt.GetEventObject()):
                proj.set_power("off")
        self.OnTimer(None)
        
    def OnTimer (self, evt):
        for proj, onoffText, shutterCheck, on_button, off_button in self.projectors:
            if proj:
                try:
                    onoffText.SetValue(proj.get_power())
                except:
                    onoffText.SetValue("offline")
                    
                try:
                    a, v = proj.get_mute()
                    shutterCheck.Enable()
                    shutterCheck.SetValue(a)
                except:
                    shutterCheck.Disable()

    def OnDestroy (self, evt):
        # Cleanup Timer
        self.timer.Stop()
        
        # Let the event pass
        evt.Skip()
        
                