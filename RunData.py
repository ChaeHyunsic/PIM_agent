import os
import sys

from win32comext.shell import shell


def getControlDataNames():
    controlDataNames = ["/Bookmarks", "/Bookmarks.bak", "/DownloadMetadata", "/Extension Cookies", "/Extension Cookies-journal", 
                        "/History", "/History-journal", "/Login Data", "/Login Data For Account", "/Login Data-journal", "/Preferences", 
                        "/Shortcuts", "/Shortcuts-journal", "/Top Sites", "/Top Sites-journal", "/Visited Links", "/Web Data", "/Web Data-journal",
                        "/Local State", "/IndexedDB", "/Session Storage", "/Sessions", "/Storage", "/Sync App Settings", "/Sync Data", "/WebStorage"]

    return controlDataNames

def getSrcPath():
    homePath = os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default/').replace('\\', '/')

    return homePath

def getDstPath():
    dstPath = "C:/Program Files/PIM_AGENT"

    return dstPath

def checkDir():
    dirPath = "C:/Program Files/PIM_AGENT"

    if(os.path.isdir(dirPath)):
        return True
    else:
        return False

def makeDir():
    ASADMIN = 'asadmin'
    dirPath = "C:/Program Files/PIM_AGENT"

    if sys.argv[-1] != ASADMIN:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:] + [ASADMIN])
        shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=params)
        sys.exit()

    os.mkdir(dirPath)
