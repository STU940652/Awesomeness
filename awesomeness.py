
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

# print c.setParameter('eParamID_XPT_Destination3_Status','9')

c = kumoManager("http://10.70.58.25")
c.getNames()
c.getSettings()

for i in range (1,17):
    print("%-15s = %s" % (c.namesDst[i], c.namesSrc[c.destSet[i]]))

