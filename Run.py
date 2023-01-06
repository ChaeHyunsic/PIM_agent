import os
import shutil
import psutil


def checkRun():
    check = 0
    srcPath = getHomePath()
    dstPath = "C:/Users/samsung/Desktop/2/"

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1

    if(check == 1):
        fileMove(dstPath, srcPath)
    elif (check == 0):
        fileMove(srcPath, dstPath)


def fileMove(srcPath, dstPath):
    filenames = getControlDataNames()

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):
            shutil.move(srcPath + filename, dstPath + filename)


def getControlDataNames():
    controlDataNames = ["History", "DownloadMetadata",
                        "Extension Cookies", "Bookmarks", "Login Data", "DownloadMetadata"]

    return controlDataNames


def getHomePath():
    homePath = os.path.expanduser(
        '~/AppData/Local/Google/Chrome/User Data/Default/').replace('\\', '/')

    return homePath


while(True):
    checkRun()
