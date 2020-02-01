import configparser
import os
import traceback

Config=configparser.SafeConfigParser()

# Put in some default values 
Config.add_section('Kumo')
Config.set('Kumo', 'ip', '')

Config.add_section('KiPro')
Config.set('KiPro', 'ip', '')

Config.add_section('ATEM')
Config.set('ATEM', 'StartCommand', 'cmd /c echo Starting')
Config.set('ATEM', 'EndCommand', 'cmd /c echo Ending')

Config.add_section('projector')
Config.set('projector', 'ip', '')

Config.add_section('FilePaths')
if "APPDATA" in os.environ:
    # For Windows
    data_directory = os.path.realpath(os.path.join(os.environ["APPDATA"], "Awesomeness"))
elif "HOME" in os.environ:
    # For *nix (untested)
    data_directory = os.path.realpath(os.path.join(os.environ["HOME"], "Awesomeness"))
else:
    data_directory = os.path.realpath(os.path.join('.', "Awesomeness"))

logging_directory = data_directory
data_directory_list = ['.',  data_directory]

# And read from the ini file
try:
    Config.read([os.path.join(d, 'settings.ini') for d in data_directory_list])
except:
    traceback.print_exc()
    pass

data_directory2 = Config.get('FilePaths','SecondaryDataDirectory', fallback = "")
if data_directory2:
    # Get data from the DataDirectory also
    try:
        Config.read([os.path.join(data_directory2,'settings.ini')])
        data_directory_list.append(data_directory2)
    except:
        traceback.print_exc()
        pass    

def write():
    global Config, data_directory
    
    if not os.path.isdir(data_directory):
        os.makedirs(data_directory)        
    
    with open (os.path.join(data_directory, 'settings.ini'), 'wt') as f:
        Config.write(f)
    