import wx
from panel_kumo import PanelKumo
from panel_kipro import PanelKipro
from panel_hs50 import PanelHS50
from panel_projectors import PanelProjector

class MainFrame (wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title)

        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu 
        menu = wx.Menu()

        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        menuKumoId = wx.NewId()
        self.menuKumo = menu.AppendCheckItem(menuKumoId, "Kumo", "Enable Kumo Panel")
        self.menuKumo.Check(True)
        self.Bind(wx.EVT_MENU, self.OnKumoMenuCheck, self.menuKumo)
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit this simple sample")

        # bind the menu event to an event handler
        #self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=wx.ID_EXIT)

        # and put the menu on the menubar
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        
        self.panelKumo = PanelKumo(self)
        self.panelKumoBlank = None
        self.panelHS50 = PanelHS50(self)
        self.panelKipro = PanelKipro(self)
        self.panelProjectors = PanelProjector(self)
        
        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.panelKumo, 1, wx.EXPAND)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.panelHS50, 1, wx.EXPAND)
        sizer2.Add(self.panelProjectors, 0, wx.EXPAND)
        sizer2.Add(self.panelKipro, 1, wx.EXPAND)
        sizer.Add(sizer2, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.panelKumo.SetupScrolling(self)
        self.panelHS50.SetupScrolling(self)
        self.panelKipro.SetupScrolling(self)
    
    def OnKumoMenuCheck (self, evt):
        if self.menuKumo.IsChecked():
            self.panelKumo = PanelKumo(self)
            self.Sizer.Replace(self.panelKumoBlank, self.panelKumo, True)
            self.panelKumoBlank.Destroy()
            self.Sizer.Show(self.panelKumo, True)
            self.panelKumo.SetupScrolling(self)
            
        else:
            self.panelKumoBlank = wx.Panel(self)
            self.Sizer.Replace(self.panelKumo, self.panelKumoBlank, True)
            self.panelKumo.Destroy()
            self.panelKumo = wx.Panel() # We really need this, but I don't know why
            self.Sizer.Hide(self.panelKumoBlank, True)
        
        self.Layout()

class MyApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()

