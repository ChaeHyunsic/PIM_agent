import psutil
import time
import keyboard
import smtplib

from PyQt5.QtWidgets import QSystemTrayIcon
from ctypes import Structure, windll, c_uint, sizeof, byref
from email.message import EmailMessage
from email.utils import formataddr

from CustomCrypto import encrypt_all_files
from RunData import getSrcPath, getDstPath, memberFileMove, guestFileRemove, genCode
from LoadingGUI import focusOnThread
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


def runGuest(var, acc):
    check = 0
    prev = var

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    var = check
    if acc < 8: #이상치 조정(최대 9)
        acc += prev + var

    if(check == 0  and acc > 0):
        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            acc = 0

            return var, acc, True

        return var, acc, False
    else:
        return var, acc, False

def runMem(flag):
    check = 0

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 0 and flag == False):
        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            return True
        return False
    elif(check == 0 and flag == True):
        return True
    else:
        return False

def trayGuest(flag):
    check = 0
    srcPath = getSrcPath()

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 0 and flag == False):
        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            emptyTrayicon = QSystemTrayIcon()
            emptyTrayicon.setVisible(False)
            emptyTrayicon.show()
            
            focusThread = focusOnThread()
            focusThread.start()
            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "개인정보 삭제 중...", 1, 1000)
            guestFileRemove(srcPath, 0)
            guestFileRemove(srcPath, 1)
            time.sleep(2)
            focusThread.terminate()
            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "개인정보를 삭제했습니다.", 1, 1000)
            keyboard.unhook_all()
            
            return True

        return False
    elif (check == 0 and flag == True):
        return flag
    else:
        return False

def encryptInTrayIcon(srcPath, dstPath, nickname, member_setting):
    emptyTrayicon = QSystemTrayIcon()
    emptyTrayicon.setVisible(False)
    emptyTrayicon.show()
    
    focusThread = focusOnThread()
    focusThread.start()

    QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "암호화 진행 중...", 1, 1000)
    memberFileMove(srcPath, dstPath, nickname, member_setting) # 파일 옮기기
    encrypt_all_files(dstPath,nickname)
    QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "암호화가 완료되었습니다.", 1, 1000)

    focusThread.terminate()
    emptyTrayicon.hide()
    keyboard.unhook_all()

def trayMem(flag, nickname, member_setting):
    check = 0
    srcPath = getSrcPath()
    dstPath = getDstPath(nickname)

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1
            break

    if(check == 0 and flag == False):
        if((int)(get_idle_duration()) >= 60):   # 타이머 설정
            encryptInTrayIcon(srcPath, dstPath, nickname, member_setting)
            return True
        return False
    elif(check == 0 and flag == True):
        return True
    else:
        return False

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
