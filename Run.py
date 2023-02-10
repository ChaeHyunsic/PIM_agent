import os
import shutil
import psutil
import time

from RunData import checkDir, makeDir, getSrcPath, getDstPath, getControlDataNames
from CustomCrypto import encrypt_all_files, decrypt_all_files


def initCheck():
    if not(checkDir()):
        makeDir()


def run(beginTimer, nickname):
    check = 0
    srcPath = getSrcPath()
    dstPath = getDstPath()

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1

    if(check == 1):
        # 파일 복호화 
        decrypt_all_files(dstPath, nickname)

        # 파일 옮기기
        fileMove(dstPath, srcPath)
    elif (check == 0):
        # 파일 옮기기
        fileMove(srcPath, dstPath)

        afterTimer = time.time()

        if((int)(afterTimer - beginTimer) == 60):   # 타이머 설정
            # 파일 암호화
            encrypt_all_files(dstPath, nickname)


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
