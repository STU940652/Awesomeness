import wx
from AJArest import kumo

class kumoManager (kumo.Client):
    namesDst = ["%i" % x for x in range (18)]
    namesSrc = ["%i" % x for x in range (18)]
    destSet = [0 for x in range (18)]
    
    def getNames (self):
        for i in range(1,17):
            # Get Destination Names
            name = "%3i: " % (i)
            name += self.getParameter('eParamID_XPT_Destination%i_Line_1' % (i))[1]
            name += ' '
            name += self.getParameter('eParamID_XPT_Destination%i_Line_2' % (i))[1]
            self.namesDst[i] = name
            
            # Get Source Name
            name = "%3s: " % (i)
            name += self.getParameter('eParamID_XPT_Source%s_Line_1' % (i))[1]
            name += ' '
            name += self.getParameter('eParamID_XPT_Source%s_Line_2' % (i))[1]
            self.namesSrc[i] = name
    
    def getSettings (self):
        for i in range(1,17):
            self.destSet[i] = int(c.getParameter('eParamID_XPT_Destination%i_Status' % (i))[1])
            
    def setChannel (self, destination, source):
        self.destSet[int(destination)] = int(source)
        # print ("setChannel", destination, source)
        # print c.setParameter('eParamID_XPT_Destination3_Status','9')

class MyFrame(wx.Frame):
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

        self.CreateStatusBar()
        

        # Now create the Panel to put the other controls on.
        panel = wx.Panel(self)
        
        # Init the Kumo stuff
        self.kumo = kumoManager("http://10.70.58.25")
        self.kumo.getNames()
        self.kumo.getSettings()
        
        sizer = wx.FlexGridSizer(3, 5, 15)
        sizer.Add(wx.StaticText(panel, -1, "Destination"))
        sizer.Add(wx.StaticText(panel, -1, "Next Source"))
        self.globalEnableSource = wx.CheckBox(panel, -1, label = "Current Source")
        self.Bind(wx.EVT_CHECKBOX, self.OnGlobalCheck, self.globalEnableSource)
        self.globalEnableSource.SetValue(False)
        sizer.Add(self.globalEnableSource)
        
        self.destControls = {}
        
        for i in range (1,17):
            tmp = {}
            destLbl = wx.StaticText (panel, -1, self.kumo.namesDst[i])
            sizer.Add(destLbl)
            nextSource = wx.ComboBox (panel, -1, style = wx.CB_READONLY,
                        choices=self.kumo.namesSrc[1:], value=self.kumo.namesSrc[self.kumo.destSet[i]])
            tmp["nextSource"] = nextSource
            self.Bind(wx.EVT_TEXT, self.OnSelectSource, nextSource)
            sizer.Add(nextSource)
            enableSource = wx.CheckBox (panel, -1, label = self.kumo.namesSrc[self.kumo.destSet[i]])
            tmp["enableSource"] = enableSource
            enableSource.SetValue(False)
            sizer.Add(enableSource)
            self.destControls[i] = tmp
            
        # Some control buttons
        sizer.AddStretchSpacer()
        applyButton = wx.Button(panel, -1, "Apply >>")
        self.Bind(wx.EVT_BUTTON, self.OnApply, applyButton)
        sizer.Add(applyButton)
        updateButton = wx.Button(panel, -1, "<< Update")
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, updateButton)
        sizer.Add(updateButton)
        
        panel.SetSizer(sizer)
        panel.Layout()

        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer()
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.CenterOnScreen(wx.BOTH)
        
        # Start a timer to get latest setting from Kumo
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2e+3) # 2 second interval
    
    def UpdateCurrent (self):
        self.kumo.getSettings()
        for dest in self.destControls:
            self.destControls[dest]["enableSource"].SetLabel(self.kumo.namesSrc[self.kumo.destSet[dest]])
        
    def OnApply (self, evt):   
        for dest in self.destControls:
            if self.destControls[dest]["enableSource"].IsChecked():
                self.kumo.setChannel(dest, self.destControls[dest]["nextSource"].GetSelection()+1)
                
        self.UpdateCurrent()
        
    def OnUpdate (self, evt):
        self.UpdateCurrent()
        for dest in self.destControls:
            self.destControls[dest]["nextSource"].SetSelection(self.kumo.destSet[dest]-1)
            
    def OnTimer (self, evt):
        self.UpdateCurrent()
        
    def OnSelectSource (self, evt):
        for dest in self.destControls:
            if self.destControls[dest]["nextSource"] == evt.GetEventObject():
                self.destControls[dest]["enableSource"].SetValue(True)
        
    def OnGlobalCheck (self, evt):            
        for dest in self.destControls:
            self.destControls[dest]["enableSource"].SetValue(self.globalEnableSource.GetValue())
        

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()

