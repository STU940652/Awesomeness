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
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit this simple sample")

        # bind the menu event to an event handler
        #self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=wx.ID_EXIT)

        # and put the menu on the menubar
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        
        #splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        #panelKumo = PanelKumo(splitter)
        #blank = wx.Panel(splitter)
        #splitter.SplitVertically(panelKumo, blank, 200)

        self.panelKumo = PanelKumo(self)
        self.panelHS50 = PanelHS50(self)
        self.panelKipro = PanelKipro(self)
        self.panelProjectors = PanelProjector(self)
        
        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        #sizer.Add(splitter, 1, wx.EXPAND)
        sizer.Add(self.panelKumo, 1, wx.EXPAND)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.panelHS50, 1, wx.EXPAND)
        sizer2.Add(self.panelProjectors, 1, wx.EXPAND)
        sizer2.Add(self.panelKipro, 1, wx.EXPAND)
        sizer.Add(sizer2, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.panelKumo.SetupScrolling(self)
        self.panelHS50.SetupScrolling(self)
        self.panelKipro.SetupScrolling(self)
        self.panelProjectors.SetupScrolling(self)

class MyApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()

