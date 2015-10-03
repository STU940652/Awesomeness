import wx
import configparser
from AJArest import kumo

presetFileName = 'presets.ini'

class kumoManager (kumo.Client):
    namesDst = ["%i" % x for x in range (17)]
    namesSrc = ["%i" % x for x in range (17)]
    destSet = [0 for x in range (17)]
    online = False
    
    def __init__ (self, url, cacheRawParameters=True):
        #try:
        #    kumo.Client.__init__(self,
        #                        url=url,
        #                        cacheRawParameters=cacheRawParameters)
        #    self.online = True
        #except:
        #    self.online = False
        pass
            
    def getNames (self):
        if self.online:
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
        if self.online:
            for i in range(1,17):
                self.destSet[i] = int(self.getParameter('eParamID_XPT_Destination%i_Status' % (i))[1])
            
    def setChannel (self, destination, source):
        if self.online:
            self.destSet[int(destination)] = int(source)
            return self.setParameter('eParamID_XPT_Destination%i_Status' %  int(destination) , str(source))

class SaveSettings (wx.Frame):
    def __init__ (self, parent, settings, namesDst, namesSrc):
        wx.Frame.__init__(self, parent, -1, "Save Preset")
        panel = wx.Panel(self)
        self.settings = settings
        self.parent = parent
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(panel, -1, "Save the following settings to a Preset"), border = 5, flag = wx.ALL)
        sizer = wx.FlexGridSizer(2, 5, 15)
        sizer.Add(wx.StaticText(panel, -1, "Destination"))
        sizer.Add(wx.StaticText(panel, -1, "Source"))
    
        for s in settings.split(','):
            destination, source = s.split('=')
            destination = int(destination)
            source = int(source)
            sizer.Add (wx.StaticText(panel, -1, namesDst[destination] + " ="))
            sizer.Add (wx.StaticText(panel, -1, namesSrc[source]))

        mainSizer.Add(sizer, border = 5, flag = wx.ALL)
        
        mainSizer.Add(wx.StaticText(panel, -1, "Preset Name"), border = 5, flag = wx.TOP)
        self.PresetName = wx.TextCtrl(panel)
        mainSizer.Add(self.PresetName, border = 5, flag = wx.ALL|wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOk = wx.Button (panel, -1, "Save")
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.btnOk)
        sizer.Add(self.btnOk)
        btnCancel = wx.Button (panel, -1, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.OnClose, btnCancel)
        sizer.Add(btnCancel)
        
        mainSizer.Add(sizer, flag = wx.ALIGN_RIGHT)
        panel.SetSizer(mainSizer)
        panel.Layout()
        # And also use a sizer to manage the size of the panel such
        # that it fills the frame
        sizer = wx.BoxSizer()
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        
    def OnClose (self, evt):
        self.Close()
        
    def OnSave (self, evt):
        # Get preset settings if they exist
        presets=configparser.SafeConfigParser()
        presets.optionxform = lambda option: option
        # And read from the ini file
        try:
            presets.read(presetFileName)
        except:
            pass
            
        presetName = self.PresetName.GetValue().strip().replace(":","")
        
        if "KumoPresets" not in presets:
            presets["KumoPresets"] = {}

        if presetName in presets["KumoPresets"]:
            pass
            # option to cancel if it exists
            d = wx.MessageDialog(self, 'Preset "' + presetName + '" already exists. \nDo you want to overwrite?',
                                style = wx.OK | wx.CANCEL)
            
            if d.ShowModal() != wx.ID_OK:
                return
                
        # Add this preset
        presets["KumoPresets"][presetName] = self.settings
        
        # And save
        with open(presetFileName, 'w') as configfile:
            presets.write(configfile)
        
        # Update parents list of presets
        self.parent.UpdatePresetList()
        
        # Done
        self.Close()

class FrameKumo (wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        self.infoBar = wx.InfoBar(self)
        
        # Init the Kumo stuff
        self.kumo = kumoManager("http://10.70.58.25")
        self.kumo.getNames()
        self.kumo.getSettings()
        if self.kumo.online:
            self.infoBar.ShowMessage("Connected to Kumo")
        else:
            self.infoBar.ShowMessage("Offline")
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.PresetSelection = wx.ComboBox(self)
        panelSizer.Add(self.PresetSelection, flag=wx.EXPAND)
        self.UpdatePresetList()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        presetLoad = wx.Button(self, -1, "Load Preset")
        self.Bind(wx.EVT_BUTTON, self.OnLoad, presetLoad)
        sizer.Add(presetLoad)
        presetSave = wx.Button(self, -1, "Save Preset")
        self.Bind(wx.EVT_BUTTON, self.OnSave, presetSave)
        sizer.Add(presetSave)
        panelSizer.Add(sizer)
        panelSizer.AddSpacer(10)
        
        sizer = wx.FlexGridSizer(3, 5, 15)
        
        sizer.Add(wx.StaticText(self, -1, "Destination"))
        sizer.Add(wx.StaticText(self, -1, "Next Source"))
        self.globalEnableSource = wx.CheckBox(self, -1, label = "Current Source")
        self.Bind(wx.EVT_CHECKBOX, self.OnGlobalCheck, self.globalEnableSource)
        self.globalEnableSource.SetValue(False)
        sizer.Add(self.globalEnableSource)
        
        self.destControls = {}
        
        for i in range (1,17):
            tmp = {}
            destLbl = wx.StaticText (self, -1, self.kumo.namesDst[i])
            sizer.Add(destLbl)
            nextSource = wx.ComboBox (self, -1, style = wx.CB_READONLY,
                        choices=self.kumo.namesSrc[1:], value=self.kumo.namesSrc[self.kumo.destSet[i]])
            tmp["nextSource"] = nextSource
            self.Bind(wx.EVT_COMBOBOX, self.OnSelectSource, nextSource)
            sizer.Add(nextSource)
            enableSource = wx.CheckBox (self, -1, label = self.kumo.namesSrc[self.kumo.destSet[i]])
            tmp["enableSource"] = enableSource
            enableSource.SetValue(False)
            sizer.Add(enableSource)
            self.destControls[i] = tmp
            
        # Some control buttons
        sizer.AddStretchSpacer()
        applyButton = wx.Button(self, -1, "Apply >>")
        self.Bind(wx.EVT_BUTTON, self.OnApply, applyButton)
        sizer.Add(applyButton)
        updateButton = wx.Button(self, -1, "<< Update")
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, updateButton)
        sizer.Add(updateButton)
        
        panelSizer.Add(sizer, flag = wx.EXPAND)
        panelSizer.Add(self.infoBar, flag = wx.EXPAND)
        self.SetSizer(panelSizer)
        self.Layout()
        
        # Start a timer to get latest setting from Kumo
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2e+3) # 2 second interval
        
    def UpdatePresetList (self):
        # Get preset settings if they exist
        self.Presets=configparser.SafeConfigParser()
        self.Presets.optionxform = lambda option: option
        # And read from the ini file
        presetNames=[]
        try:
            self.Presets.read(presetFileName)
            presetNames = self.Presets.options("KumoPresets")
        except:
            pass
            
        self.PresetSelection.Set(presetNames)
    
    def UpdateCurrent (self):
        self.kumo.getSettings()
        for dest in self.destControls:
            self.destControls[dest]["enableSource"].SetLabel(self.kumo.namesSrc[self.kumo.destSet[dest]])

    def OnSave (self, evt):
        settings = ""
        for dest in self.destControls:
            if self.destControls[dest]["enableSource"].IsChecked():
                settings += "%i=%i," % (dest, self.destControls[dest]["nextSource"].GetSelection()+1)
        settings = settings.strip(',')
        
        m = SaveSettings(self, settings, self.kumo.namesDst, self.kumo.namesSrc)
        m.Show(True)
    
    def OnLoad (self, evt):
        settings = self.Presets["KumoPresets"][self.PresetSelection.GetValue()]
        for s in settings.split(','):
            destination, source = s.split('=')
            dest = int(destination)
            source = int(source)-1
            self.destControls[dest]["nextSource"].SetSelection(source)
            if self.destControls[dest]["nextSource"].GetValue() == self.destControls[dest]["enableSource"].GetLabel():
                self.destControls[dest]["enableSource"].SetValue(False)
            else:
                self.destControls[dest]["enableSource"].SetValue(True)

    def OnApply (self, evt):   
        for dest in self.destControls:
            #print (self.destControls[dest]["enableSource"].IsChecked())
            if self.destControls[dest]["enableSource"].IsChecked():
                self.kumo.setChannel(dest, self.destControls[dest]["nextSource"].GetSelection()+1)
                
        # Clear check boxes
        for dest in self.destControls:
            self.destControls[dest]["enableSource"].SetValue(self.globalEnableSource.GetValue())

        # Update        
        self.UpdateCurrent()
        
        # Redraw screen
        self.Layout()
        
    def OnUpdate (self, evt):
        self.UpdateCurrent()
        for dest in self.destControls:
            self.destControls[dest]["nextSource"].SetSelection(self.kumo.destSet[dest]-1)

        # Clear check boxes
        for dest in self.destControls:
            self.destControls[dest]["enableSource"].SetValue(self.globalEnableSource.GetValue())
            
    def OnTimer (self, evt):
        self.UpdateCurrent()
        
    def OnSelectSource (self, evt):
        for dest in self.destControls:
            if self.destControls[dest]["nextSource"] == evt.GetEventObject():
                if self.destControls[dest]["nextSource"].GetValue() == self.destControls[dest]["enableSource"].GetLabel():
                    self.destControls[dest]["enableSource"].SetValue(False)
                else:
                    self.destControls[dest]["enableSource"].SetValue(True)
        
    def OnGlobalCheck (self, evt):            
        for dest in self.destControls:
            self.destControls[dest]["enableSource"].SetValue(self.globalEnableSource.GetValue())
        
