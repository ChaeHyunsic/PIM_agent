import os
import psutil
import time
import webbrowser

from RunData import getSrcPath, getDstPath, memberFileMove, guestFileRemove
from LoadingGUI import DecryptLoadingClass, EncryptLoadingClass, preGuestClass


def runGuest(beginTimer, flag):
    check = 0
    srcPath = getSrcPath()

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 0 and flag == False):
        guestFileRemove(srcPath, 0)

        afterTimer = time.time()

        if((int)(afterTimer - beginTimer) >= 10):   # 타이머 설정
            preGuestThread = preGuestClass(srcPath)
            preGuestThread.exec()

            return beginTimer, True

        return beginTimer, False
    elif (check == 0 and flag == True):
        return beginTimer, flag
    else:
        beginTimer = time.time()

        return beginTimer, False


def runMem(beginTimer, flag, nickname):
    check = 0
    srcPath = getSrcPath()
    dstPath = getDstPath(nickname)

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 1 and flag == 0):
        # 파일 옮기기
        memberFileMove(dstPath, srcPath, nickname)

        beginTimer = time.time()

        return beginTimer, 0
    elif(check == 1 and flag == 1):
        os.system('taskkill /f /im chrome.exe')

        decryptThread = DecryptLoadingClass(dstPath, nickname)
        decryptThread.exec()

        # 파일 옮기기
        memberFileMove(dstPath, srcPath, nickname)

        webbrowser.open("https://google.com")
        beginTimer = time.time()

        return beginTimer, 0
    elif (check == 0 and flag == 0):
        # 파일 옮기기
        memberFileMove(srcPath, dstPath, nickname)

        afterTimer = time.time()

        if((int)(afterTimer - beginTimer) >= 10):   # 타이머 설정
            encryptThread = EncryptLoadingClass(srcPath, dstPath, nickname)
            encryptThread.exec()

            return beginTimer, 1
        else:
            return beginTimer, 0
    elif (check==0 and flag == 1):
        return beginTimer, 1

