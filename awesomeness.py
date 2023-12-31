import wx
from panel_kumo import PanelKumo
from panel_kipro import PanelKipro
from panel_atem import PanelATEM
from panel_projectors import PanelProjector
import os
import Settings
import logging
import sys

class PanelManager():    
    def __init__ (self, parent, thisClass, menuCheck, parentSizer, proportion = 1):
        self.thisClass = thisClass
        self.menuCheck = menuCheck
        self.parentSizer = parentSizer
        self.parent = parent
        self.proportion = proportion
        self.panelMain =  None
        self.panelBlank =  None

        # Create panel and add it to the sizer
        if self.menuCheck.IsChecked():
            self.panelMain = self.thisClass(self.parent)
            self.parentSizer.Add(self.panelMain, proportion, wx.EXPAND)
            self.parentSizer.Show(self.panelMain, True) 
            self.MainDisplayed = True
            
        else:
            self.panelBlank =  wx.Panel(self.parent)
            self.parentSizer.Add(self.panelBlank, proportion, wx.EXPAND)
            self.parentSizer.Hide(self.panelBlank, True)
            self.MainDisplayed = False
        
    def OnMenuCheck (self, evt = None):
        if self.menuCheck.IsChecked():
            self.panelMain = self.thisClass(self.parent)
            self.parentSizer.Replace(self.panelBlank, self.panelMain, True)
            self.parentSizer.Show(self.panelMain, True)
            self.MainDisplayed = True
            self.panelBlank.Destroy()
            self.panelBlank = None
            self.SetupScrolling(self.parent)
            
        else:
            self.panelBlank =  wx.Panel(self.parent)
            self.parentSizer.Replace(self.panelMain, self.panelBlank, True)
            self.panelMain.Destroy()
            self.panelMain = wx.Panel() # We really need this, but I don't know why
            self.parentSizer.Hide(self.panelBlank, True)
            self.MainDisplayed = False
        
        self.parentSizer.Layout()
        
    def SetupScrolling(self, dummy = None):
        if self.proportion and self.MainDisplayed:
            self.panelMain.SetupScrolling(self.parent)
        

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
        
        menu = wx.Menu()
        self.menuKumo = menu.AppendCheckItem(wx.ID_ANY, "Kumo", "Enable Kumo Panel")
        self.menuKumo.Check(Settings.Config.getboolean("Kumo", "show", fallback=True))
        self.Bind(wx.EVT_MENU, self.OnKumoMenuCheck, self.menuKumo)
        self.menuATEM = menu.AppendCheckItem(wx.ID_ANY, "ATEM", "Enable ATEM Panel")
        self.menuATEM.Check(Settings.Config.getboolean("ATEM", "show", fallback=True))
        self.Bind(wx.EVT_MENU, self.OnATEMMenuCheck, self.menuATEM)
        self.menuProj = menu.AppendCheckItem(wx.ID_ANY, "Projectors", "Enable Projector Panel")
        self.menuProj.Check(Settings.Config.getboolean("projector", "show", fallback=True))
        self.Bind(wx.EVT_MENU, self.OnProjMenuCheck, self.menuProj)
        self.menuKiPro = menu.AppendCheckItem(wx.ID_ANY, "KiPro", "Enable KiPro Panel")
        self.menuKiPro.Check(Settings.Config.getboolean("KiPro", "show", fallback=True))
        self.Bind(wx.EVT_MENU, self.OnKiProMenuCheck, self.menuKiPro)
        menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.OnViewSave, menu.Append(wx.ID_ANY, "Save Settings", "Save the view settings"))
        
        menuBar.Append(menu, "&View")
        
        self.SetMenuBar(menuBar)
        
        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panelKumo = PanelManager (self, PanelKumo, self.menuKumo, sizer) #sizer.Add(self.panelKumo, 1, wx.EXPAND)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.panelATEM = PanelManager (self, PanelATEM, self.menuATEM, sizer2) #sizer2.Add(self.panelATEM, 1, wx.EXPAND)
        self.panelProjectors = PanelManager (self, PanelProjector, self.menuProj, sizer2, 0) #sizer2.Add(self.panelProjectors, 0, wx.EXPAND)
        self.panelKiPro = PanelManager (self, PanelKipro, self.menuKiPro, sizer2) #sizer2.Add(self.panelKipro, 1, wx.EXPAND)
        sizer.Add(sizer2, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        
        self.panelKumo.SetupScrolling(self)
        self.panelATEM.SetupScrolling(self)
        #self.panelProjectors.SetupScrolling(self)
        self.panelKiPro.SetupScrolling(self)
    
    def OnKumoMenuCheck (self, evt):
        self.panelKumo.OnMenuCheck()
        
    def OnATEMMenuCheck (self, evt):
        self.panelATEM.OnMenuCheck()

    def OnProjMenuCheck (self, evt):
        self.panelProjectors.OnMenuCheck()

    def OnKiProMenuCheck (self, evt):
        self.panelKiPro.OnMenuCheck()
        
    def OnViewSave (self, evt):
        Settings.Config.set("Kumo", "show", str(self.menuKumo.IsChecked()))
        Settings.Config.set("ATEM", "show", str(self.menuATEM.IsChecked()))
        Settings.Config.set("projector", "show", str(self.menuProj.IsChecked()))
        Settings.Config.set("KiPro", "show", str(self.menuKiPro.IsChecked()))
        Settings.write()

        
class MyApp(wx.App):
    def OnInit(self):
        logging.info("##### Preparing Awesomeness #####")
        frame = MainFrame(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

if __name__ == "__main__":
    if not os.path.isdir(Settings.logging_directory):
        os.makedirs(Settings.logging_directory)
    logging.basicConfig(filename=os.path.join(Settings.logging_directory,'awesomeness.log'), 
        level=logging.INFO, 
        format='%(asctime)s:%(levelname)s:%(message)s')  

    sys.excepthook = handle_exception
        
    app = MyApp(redirect=False)
    app.MainLoop()
    logging.info("##### Ending Awesomeness #####")
