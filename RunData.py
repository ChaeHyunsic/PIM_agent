import os
import sys

from win32comext.shell import shell
from DB_setting import getCustomSetting


def getControlDataNames(nickname):
    checkRetval = getCustomSetting(nickname)
    controlDataNames = []

    if checkRetval[0] == 1:
        controlDataNames.extend(["/Bookmarks", "/Bookmarks.bak"])
    if checkRetval[1] == 1:
        controlDataNames.extend(["/History", "/History-journal", "/Visited Links"])
    if checkRetval[2] == 1:
        controlDataNames.extend(["/DownloadMetadata"])
    if checkRetval[3] == 1:
        controlDataNames.extend(["/Login Data", "/Login Data For Account", "/Login Data-journal", "/Preferences", "/Shortcuts", 
                                    "/Shortcuts-journal", "/Top Sites", "/Top Sites-journal", "/Web Data", "/Web Data-journal", 
                                    "/Local State", "/IndexedDB", "/Storage", "/Sync App Settings", "/Sync Data", "/WebStorage"])

    return controlDataNames

def getRemoveDataNames(nickname):
    checkRetval = getCustomSetting(nickname)
    removeDataNames = []

    if checkRetval[4] == 1:
        removeDataNames.extend(["/Cookies"])
    if checkRetval[5] == 1:
        removeDataNames.extend(["/cache", "/Code cache", "DawnCache"])
    if checkRetval[6] == 1:
        removeDataNames.extend(["/Session Storage", "/Sessions"])

    return removeDataNames

def getSrcPath():
    homePath = os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default').replace('\\', '/')

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
