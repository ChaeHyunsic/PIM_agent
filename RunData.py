import os
import shutil
import random
import math
import time

from CustomCrypto import decrypt_all_files

def getControlDataNames(nickname, member_setting):
    if(nickname == None):
        member_setting = [1,1,1,1,1,1,1]

    controlDataNames = []

    if member_setting[0] == 1:
        controlDataNames.extend(["/Bookmarks", "/Bookmarks.bak"])
    if member_setting[1] == 1:
        controlDataNames.extend(["/History", "/History-journal", "/Visited Links"])
    if member_setting[2] == 1:
        controlDataNames.extend(["/DownloadMetadata"])
    if member_setting[3] == 1:
        controlDataNames.extend(["/Login Data", "/Login Data For Account", "/Login Data-journal", "/Preferences", "/Shortcuts", 
                                    "/Shortcuts-journal", "/Top Sites", "/Top Sites-journal", "/Web Data", "/Web Data-journal", 
                                    "/Local State", "/IndexedDB", "/Storage", "/Sync App Settings", "/Sync Data", "/WebStorage"])

    return controlDataNames

def getRemoveDataNames(nickname, member_setting):
    if(nickname == None):
        member_setting = [1,1,1,1,1,1,1]

    removeDataNames = []

    if member_setting[4] == 1:
        removeDataNames.extend(["/Cookies"])
    if member_setting[5] == 1:
        removeDataNames.extend(["/cache", "/Code cache", "DawnCache"])
    if member_setting[6] == 1:
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

def initLocalCheck(nickname, member_setting):
    srcPath = getSrcPath()
    dstPath = os.path.expanduser('~/AppData/Local/PIM_AGENT/').replace('\\', '/') + nickname

    if(not os.path.isdir(dstPath)):
        os.mkdir(dstPath)
        time.sleep(0.1)

    decrypt_all_files(dstPath, nickname)

    # 파일 옮기기
    memberFileMove(dstPath, srcPath, nickname, member_setting)

def memberFileMove(srcPath, dstPath, nickname, member_setting):
    filenames = getControlDataNames(nickname, member_setting)

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):
            if(os.path.exists(dstPath + filename)):
                os.remove(dstPath + filename)
            shutil.move(srcPath + filename, dstPath + filename)

        elif(os.path.isdir(srcPath + filename)):
            if(os.path.exists(dstPath + filename)):
                shutil.rmtree(dstPath + filename)
            shutil.move(srcPath + filename, dstPath + filename)

def memberFileRemove(srcPath, nickname, member_setting):
    filenames = getRemoveDataNames(nickname, member_setting)
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
        filenames = getControlDataNames(None, None)
    else:
        filenames = getRemoveDataNames(None, None)

    for filename in filenames:
        if(os.path.exists(srcPath + filename) and os.path.isfile(srcPath + filename)):
            os.remove(srcPath + filename)

        elif(os.path.exists(srcPath + filename) and os.path.isdir(srcPath + filename)):
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

def genCode():
    digits = [i for i in range(0, 10)]

    code = ""
    
    for i in range(6):
        index = math.floor(random.random() * 10)
        code += str(digits[index])
    
    return code
    