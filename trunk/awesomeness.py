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
        globalEnableSource = wx.CheckBox(panel, -1, label = "Current Source")
        globalEnableSource.SetValue(True)
        sizer.Add(globalEnableSource)
        
        for i in range (1,17):
            destLbl = wx.StaticText (panel, -1, self.kumo.namesDst[i])
            sizer.Add(destLbl)
            nextSource = wx.ComboBox (panel, -1, choices=self.kumo.namesSrc, value=self.kumo.namesSrc[self.kumo.destSet[i]])
            sizer.Add(nextSource)
            enableSource = wx.CheckBox (panel, -1, label = self.kumo.namesSrc[self.kumo.destSet[i]])
            enableSource.SetValue(True)
            sizer.Add(enableSource)
            #currentSource = wx.StaticText (panel, -1, self.kumo.namesSrc[self.kumo.destSet[i]])
            #sizer.Add(currentSource)

        # Some control buttons
        sizer.AddStretchSpacer()
        applyButton = wx.Button(panel, -1, "Apply >>")
        sizer.Add(applyButton)
        updateButton = wx.Button(panel, -1, "<< Update")
        sizer.Add(updateButton)
        
        
        
        ## and a few controls
        #text = wx.StaticText(panel, -1, "Hello World!  Welcome to wxPython.")
        #text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        #text.SetSize(text.GetBestSize())
        #btn = wx.Button(panel, -1, "Close")
        #funbtn = wx.Button(panel, -1, "Just for fun...")
        #
        ## bind the button events to handlers
        #self.Bind(wx.EVT_BUTTON, self.OnTimeToClose, btn)
        #self.Bind(wx.EVT_BUTTON, self.OnFunButton, funbtn)
        #
        ## Use a sizer to layout the controls, stacked vertically and with
        ## a 10 pixel border around each
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(text, 0, wx.ALL, 10)
        #sizer.Add(btn, 0, wx.ALL, 10)
        #sizer.Add(funbtn, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        panel.Layout()

        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer()
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.CenterOnScreen(wx.BOTH)
        
            

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "Awesomeness")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()


            
# print c.setParameter('eParamID_XPT_Destination3_Status','9')

#c = kumoManager("http://10.70.58.25")
#c.getNames()
#c.getSettings()
#
#for i in range (1,17):
#    print("%-15s = %s" % (c.namesDst[i], c.namesSrc[c.destSet[i]]))

