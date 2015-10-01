import wx
from frame_kumo import FrameKumo

class MyApp(wx.App):
    def OnInit(self):
        frame = FrameKumo(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()

