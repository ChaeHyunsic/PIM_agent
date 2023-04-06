import os
import psutil
import time
import webbrowser
from PyQt5.QtWidgets import QSystemTrayIcon
from ctypes import Structure, windll, c_uint, sizeof, byref
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from CustomCrypto import encrypt_all_files, decrypt_all_files
from RunData import getSrcPath, getDstPath, memberFileMove, guestFileRemove, genCode
from LoadingGUI import DecryptLoadingClass, EncryptLoadingClass, preGuestClass, focusOnThread
from DB_setting import getAgentEmail

#input 여부 확인 -> input 없을시 타이머 시작 및 반환
class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime

    return millis / 1000.0


def runGuest(flag):
    check = 0
    srcPath = getSrcPath()

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 0 and flag == False):
        guestFileRemove(srcPath, 0)

        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            preGuestThread = preGuestClass(srcPath)
            preGuestThread.exec()

            return True

        return False
    elif (check == 0 and flag == True):
        return flag
    else:
        return False

def runMem(flag, nickname):
    check = 0
    srcPath = getSrcPath()
    dstPath = getDstPath(nickname)

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 1 and flag == False):
        # 파일 옮기기
        memberFileMove(dstPath, srcPath, nickname)

        return False
    elif(check == 1 and flag == True):
        os.system('taskkill /f /im chrome.exe')

        decryptThread = DecryptLoadingClass(dstPath, nickname)
        decryptThread.exec()

        # 파일 옮기기
        memberFileMove(dstPath, srcPath, nickname)

        webbrowser.open("https://google.com")

        return False
    elif (check == 0 and flag == False):
        # 파일 옮기기
        memberFileMove(srcPath, dstPath, nickname)

        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            encryptThread = EncryptLoadingClass(srcPath, dstPath, nickname)
            encryptThread.exec()

            return True
        else:
            return False
    elif (check==0 and flag == True):
        return True

def trayGuest(flag):
    check = 0
    srcPath = getSrcPath()

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 0 and flag == False):
        guestFileRemove(srcPath, 0)

        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            emptyTrayicon = QSystemTrayIcon()
            emptyTrayicon.setVisible(False)
            emptyTrayicon.show()
            
            focusThread = focusOnThread()
            focusThread.start()
            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "개인정보 삭제 중...", 1, 1000)
            guestFileRemove(srcPath, 1)
            time.sleep(2)
            focusThread.stop()
            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "개인정보를 삭제했습니다.", 1, 1000)
            
            return True

        return False
    elif (check == 0 and flag == True):
        return flag
    else:
        return False

def trayMem(flag, nickname):
    check = 0
    srcPath = getSrcPath()
    dstPath = getDstPath(nickname)

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 1 and flag == False):
        # 파일 옮기기
        memberFileMove(dstPath, srcPath, nickname)

        return False

    elif(check == 1 and flag == True):
        os.system('taskkill /f /im chrome.exe')

        emptyTrayicon = QSystemTrayIcon()
        emptyTrayicon.setVisible(False)
        emptyTrayicon.show()
        
        focusThread = focusOnThread()
        focusThread.start()
        QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "복호화 진행 중...", 1, 1000)
        time.sleep(1)
        decrypt_all_files(dstPath,nickname)
        QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "복호화가 완료되었습니다.", 1, 1000)
        time.sleep(1)
        focusThread.terminate()
        emptyTrayicon.hide()
        
        # 파일 옮기기
        memberFileMove(dstPath, srcPath, nickname)

        webbrowser.open("https://google.com")

        return False
    elif (check == 0 and flag == False):
        # 파일 옮기기
        memberFileMove(srcPath, dstPath, nickname)

        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            emptyTrayicon = QSystemTrayIcon()
            emptyTrayicon.setVisible(False)
            emptyTrayicon.show()
            
            focusThread = focusOnThread()
            focusThread.start()
            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "암호화 진행 중...", 1, 1000)
            time.sleep(1)
            encrypt_all_files(dstPath,nickname)
            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "암호화가 완료되었습니다.", 1, 1000)
            time.sleep(1)
            focusThread.terminate()
            emptyTrayicon.hide()
            return True
        else:
            return False
    elif (check==0 and flag == True):
        return True

def sendMail(address):

    code = genCode()

    # 이메일 주소와 암호 입력
    MY_ADDRESS, MY_PASSWORD = getAgentEmail()

    # 수신자 이메일 주소 입력
    TO_ADDRESS = address

    # 이메일 구성
    message = EmailMessage()

    message['From'] = formataddr(('PIM AGENT', MY_ADDRESS))
    message['To'] = TO_ADDRESS
    message['Subject'] = '[PIM AGENT] 비밀번호 재설정을 하기위한 메시지 입니다.'

    # 이메일 내용 입력
    body = '비밀번호를 재설정 하기 위해\n해당 6자리 코드({})를 입력해 주세요'.format(code)
    message.set_content(body)

    # SMTP 서버 설정 및 이메일 보내기
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(MY_ADDRESS, MY_PASSWORD)
        smtp.send_message(message)

    return code
