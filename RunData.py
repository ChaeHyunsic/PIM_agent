import os
import shutil

from DB_setting import getCustomSetting
from CustomCrypto import decrypt_all_files

def getControlDataNames(nickname):
    if(nickname == None):
        checkRetval = [1,1,1,1,1,1,1]
    else:
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
    if(nickname == None):
        checkRetval = [1,1,1,1,1,1,1]
    else:
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

def getDstPath(nickname):
    dstPath = os.path.expanduser('~/AppData/Local/PIM_AGENT/').replace('\\', '/') + nickname

    return dstPath

def initCheck():
    dirPath = os.path.expanduser('~/AppData/Local/PIM_AGENT').replace('\\', '/')

    if(not os.path.isdir(dirPath)):
        os.mkdir(dirPath)

def initLocalCheck(nickname):
    srcPath = getSrcPath()
    dstPath = os.path.expanduser('~/AppData/Local/PIM_AGENT/').replace('\\', '/') + nickname

    if(not os.path.isdir(dstPath)):
        os.mkdir(dstPath)

    decrypt_all_files(dstPath, nickname)

    # 파일 옮기기
    memberFileMove(dstPath, srcPath, nickname)

def memberFileMove(srcPath, dstPath, nickname):
    filenames = getControlDataNames(nickname)

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):
            if(os.path.exists(dstPath + filename)):
                os.remove(dstPath + filename)
            shutil.move(srcPath + filename, dstPath + filename)

        elif(os.path.isdir(srcPath + filename)):
            if(os.path.exists(dstPath + filename)):
                shutil.rmtree(dstPath + filename)
            shutil.move(srcPath + filename, dstPath + filename)

def memberFileRemove(srcPath, nickname):
    filenames = getRemoveDataNames(nickname)
    multiProfilePath = srcPath.replace('\\', '/')[:-8]
    multiProfilenames = getMultiProfilenames()

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):
            os.remove(srcPath + filename)

        elif(os.path.isdir(srcPath + filename)):
            shutil.rmtree(srcPath + filename)

    i = 1
    while(os.path.exists(multiProfilePath + multiProfilenames[0] + str(i))):
        shutil.rmtree(multiProfilePath + multiProfilenames[0] + str(i))
        if(os.path.exists(multiProfilePath + multiProfilenames[1])):
            os.remove(multiProfilePath + multiProfilenames[1])
        i += 1

def guestFileRemove(srcPath, flag):
    multiProfilePath = srcPath.replace('\\', '/')[:-8]
    multiProfilenames = getMultiProfilenames()

    if(flag == 0):
        filenames = getControlDataNames(None)
    else:
        filenames = getRemoveDataNames(None)

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):
            os.remove(srcPath + filename)

        elif(os.path.isdir(srcPath + filename)):
            shutil.rmtree(srcPath + filename)
    
    i = 1
    while(os.path.exists(multiProfilePath + multiProfilenames[0] + str(i))):
        shutil.rmtree(multiProfilePath + multiProfilenames[0] + str(i))
        if(os.path.exists(multiProfilePath + multiProfilenames[1])):
            os.remove(multiProfilePath + multiProfilenames[1])
        i += 1

def getMultiProfilenames():
    multiProfilenames = []
    multiProfilenames.extend(["/Profile ", "/Local State"])

    return multiProfilenames
