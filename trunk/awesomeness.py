import wx
from panel_kumo import PanelKumo
from panel_kipro import PanelKipro

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

        panelKumo = PanelKumo(self)
        panelKipro = PanelKipro(self)
        
        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        #sizer.Add(splitter, 1, wx.EXPAND)
        sizer.Add(panelKumo, 1, wx.EXPAND)
        sizer.Add(panelKipro, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        


class MyApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()

