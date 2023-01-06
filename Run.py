import os
import shutil
import psutil

from RunData import *


def initCheck():
    if not(checkDir()):
        makeDir()


def run():
    check = 0
    srcPath = getSrcPath()
    dstPath = getDstPath()

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


initCheck()

while(True):
    run()
