import os
import shutil
import psutil
import time

from RunData import *
from CustomCrypto import *


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
        # 파일 복호화 (로그인 기능 구현되면 로그인 성공시 실행되도록)
        #decrypt_all_files(dstPath)

        # 파일 옮기기
        fileMove(dstPath, srcPath)
    elif (check == 0):
        # 파일 옮기기
        fileMove(srcPath, dstPath)

        afterTimer = time.time()

        if((int)(afterTimer - beginTimer) == 60):   # 타이머 설정
            # 파일 암호화
            encrypt_all_files(dstPath)


def fileMove(srcPath, dstPath):
    filenames = getControlDataNames()

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):
            if(os.path.exists(dstPath + filename)):
                os.remove(dstPath + filename)
            shutil.move(srcPath + filename, dstPath + filename)

        elif(os.path.isdir(srcPath + filename)):
            if(os.path.exists(dstPath + filename)):
                shutil.rmtree(dstPath + filename)
            shutil.move(srcPath + filename, dstPath + filename)


initCheck()

beginTimer = time.time()

while(True):
    run()
