import configparser
import os

Config=configparser.SafeConfigParser()

# Put in some default values 
Config.add_section('Kumo')
Config.set('Kumo', 'ip', '')

Config.add_section('KiPro')
Config.set('KiPro', 'ip', '')

Config.add_section('HS50')
Config.set('HS50', 'ip', '')
Config.set('HS50', 'KiProChannel', '3')

Config.add_section('projector')
Config.set('projector', 'ip', '')

Config.add_section('FilePaths')
if "APPDATA" in os.environ:
    # For Windows
    Config.set('FilePaths', 'LogPath', os.path.realpath(os.path.join(os.environ["APPDATA"], "TrimmerData")))
elif "HOME" in os.environ:
    # For *nix (untested)
    Config.set('FilePaths', 'LogPath', os.path.realpath(os.path.join(os.environ["HOME"], "TrimmerData")))
else:
    Config.set('FilePaths', 'LogPath', os.path.realpath(os.path.join('.', "TrimmerData")))


# And read from the ini file
try:
    Config.read(['settings.ini', os.path.join(Config.get('FilePaths', 'LogPath'),'settings.ini')])
except:
    pass
    
def write():
    global Config
    with open ('settings.ini', 'wt') as f:
        Config.write(f)
    