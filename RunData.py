import os
import sys

from win32comext.shell import shell


def getControlDataNames():
    controlDataNames = ["History", "DownloadMetadata", "Extension Cookies", "Bookmarks", "Login Data", "DownloadMetadata"]

    return controlDataNames

def getSrcPath():
    homePath = os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default/').replace('\\', '/')

    return homePath

def getDstPath():
    dstPath = "C:/Program Files/PIM_AGENT/"

    return dstPath

def checkDir():
    dirPath = "C:/Program Files/PIM_AGENT"

    if(os.path.isdir(dirPath)):
        return True
    else:
        return False

def makeDir():
    ASADMIN = 'asadmin'

    if sys.argv[-1] != ASADMIN:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:] + [ASADMIN])
        shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=params)
        sys.exit()
