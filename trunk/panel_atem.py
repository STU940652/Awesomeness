import wx
import wx.lib.scrolledpanel 
import Settings
import subprocess

class PanelATEM (wx.lib.scrolledpanel.ScrolledPanel):

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style = wx.BORDER_SIMPLE)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.infoBar = wx.StaticText(self, -1, "Video Switcher")
        panelSizer.Add(self.infoBar)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddStretchSpacer(1)
        self.startButton = wx.Button (self, -1, "Start Macro")
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.startButton)
        sizer.Add(self.startButton)
        sizer.AddStretchSpacer(1)
        self.endButton = wx.Button (self, -1, "End Macro")
        self.Bind(wx.EVT_BUTTON, self.OnEnd, self.endButton)
        sizer.Add(self.endButton)
        sizer.AddStretchSpacer(1)
        panelSizer.Add(sizer, border = 5, flag=wx.EXPAND)
        
        panelSizer.AddStretchSpacer()
        self.SetSizer(panelSizer)
        self.Layout()
                
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
        self.Fit()
        s = self.Sizer.ComputeFittingWindowSize(self)
        self.SetMaxSize((-1,s[1]))
        
        self.command_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnCleanup, self.command_timer)
        
        self.command_subprocess = None
        
        self.OnInit()

    def OnInit (self, evt=None):
        self.OnCleanup()
        self.command_subprocess = subprocess.Popen(args=Settings.Config['ATEM']['InitCommand'])
        self.command_timer.StartOnce(5000)
        
    def OnStart (self, evt=None):
        self.OnCleanup()
        self.command_subprocess = subprocess.Popen(args=Settings.Config['ATEM']['StartCommand'])
        self.command_timer.StartOnce(5000)
        
    def OnEnd (self, evt=None):
        self.OnCleanup()
        self.command_subprocess = subprocess.Popen(args=Settings.Config['ATEM']['EndCommand'])
        self.command_timer.StartOnce(5000)
        
    def OnCleanup (self, evt=None):
        # Called 5 seconds after OnStart/OnEnd to make sure the subprocess doesn't stall
        if self.command_subprocess == None:
            return
            
        if self.command_subprocess.poll() == None:
            self.command_subprocess.kill()
            
        self.command_subprocess = None
                
    def OnDestroy (self, evt):
        # Cleanup Timer
        self.command_timer.Stop()
        
        # Let the event pass
        evt.Skip()
        