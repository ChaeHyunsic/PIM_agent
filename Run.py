import psutil
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

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),                     # 구조체 필드: cbSize (unsigned int 형)
        ('dwTime', c_uint),                     # 구조체 필드: dwTime (unsigned int 형)
    ]

# idle한 시간 측정 메서드
def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()                                     # LASTINPUTINFO 구조체 생성
    lastInputInfo.cbSize = sizeof(lastInputInfo)                        # 구조체의 크기 설정

    windll.user32.GetLastInputInfo(byref(lastInputInfo))                # lastInputInfo 정보 업데이트
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime      # 현재 Tick에서 마지막 입력 시간을 빼서 idle한 시간 계산

    return millis / 1000.0                                              # 밀리초를 초로 변환

# 비 로그인 상태에서 수행하는 메서드
def runGuest(var, acc):
    check = 0 
    prev = var                              # 이전 실행값을 prev 변수에 할당

    for proc in psutil.process_iter():      # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":         # 현재 프로세스 이름이 "chrome.exe"인 경우
            check = 1                       # 크롬 실행 플래그 세팅
            break                           

    var = check                     
    if acc < 8:                             # 이상치 조정(최대 9)
        acc += prev + var                   # acc값 누적

    if(check == 0  and acc > 0):                    # 크롬이 꺼져있고 이전에 크롬이 커졌다 꺼진 경우
        if((int)(get_idle_duration()) >= 60):       # idle한 시간이 threshold 이상인 경우
            acc = 0                                 # 0으로 초기화

            return var, acc, True                   # 시그널 emit 플래그 세팅       

        return var, acc, False
    else:
        return var, acc, False
    
# 로그인된 상태에서 수행하는 메서드
def runMem(flag):
    check = 0                              

    for proc in psutil.process_iter():      # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":         # 현재 프로세스 이름이 "chrome.exe"인 경우
            check = 1                       # 크롬 실행 플래그 세팅 
            break                           

    if(check == 0 and flag == False):               # 크롬이 꺼져있고 암호화를 실행하지 않은 경우
        if((int)(get_idle_duration()) >= 60):       # idle한 시간이 threshold 이상인 경우
            return True                             # 시그널 emit 플래그 세팅
        return False
    elif(check == 0 and flag == True):              # 크롬이 꺼져있고 암호화를 실행 한 경우
        return True                                 # 시그널 emit 플래그 세팅
    else:                                       
        return False
        
# 비 로그인 상태에서 trayicon이 수행하는 메서드
def trayGuest(flag):
    check = 0                               
    srcPath = getSrcPath()                  # 크롬에서 지정한 개인정보 폴더 경로 할당

    for proc in psutil.process_iter():      # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":         # 현재 프로세스 이름이 "chrome.exe"인 경우
            check = 1                       # 크롬 실행 플래그 세팅
            break                           

    if(check == 0 and flag == False):               # 크롬이 꺼져있고 파일 삭제를 한번도 하지 않은 경우
        if((int)(get_idle_duration()) >= 60):       # idle한 시간이 threshold 이상인 경우
            emptyTrayicon = QSystemTrayIcon()       # 빈 시스템 트레이 아이콘을 생성
            emptyTrayicon.setVisible(False)         # 시스템 트레이 아이콘이 표시되지 않도록 설정
            emptyTrayicon.show()                    # 시스템 트레이 아이콘을 출력
            
            focusThread = focusOnThread()           # focusOnThread 스레드 객체 생성
            focusThread.start()                     # 스레드 시작

            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "개인정보 삭제 중...", 1, 1000)         # 시스템 트레이 아이콘에 메시지를 1초 동안 표시

            guestFileRemove(srcPath, 0)                                                               # srcPath에 있는 파일 삭제
            guestFileRemove(srcPath, 1)                                                               # srcPath에 있는 파일 삭제
            focusThread.terminate()                                                                   # 스레드 종료

            QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "개인정보를 삭제했습니다.", 1, 1000)     # 시스템 트레이 아이콘에 메시지를 1초 동안 표시

            keyboard.unhook_all()                                                                     # 키보드 후킹 모두 해제
            
            return True                         # 중복 실행 방지 플래그 세팅                         
        return False                            # idle한 상태가 타임아웃보다 적은 상태
    elif (check == 0 and flag == True):         # 크롬이 꺼져있고 파일 삭제를 이미 한 상태
        return flag                             # 현 상태 유지
    else:                                       
        return False                    

# trayicon 상태에서 암호화 기능을 수행하는 메서드 정의
def encryptInTrayIcon(srcPath, dstPath, nickname, member_setting):
    emptyTrayicon = QSystemTrayIcon()                                                   # 빈 시스템 트레이 아이콘을 생성
    emptyTrayicon.setVisible(False)                                                     # 시스템 트레이 아이콘이 표시되지 않도록 설정
    emptyTrayicon.show()                                                                # 시스템 트레이 아이콘을 출력
    
    focusThread = focusOnThread()                                                       # focusOnThread 스레드 객체 생성
    focusThread.start()                                                                 # 스레드 시작

    QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "암호화 진행 중...", 1, 1000)    # 시스템 트레이 아이콘에 메시지를 1초 동안 표시 

    while(True):            
        try:
            memberFileMove(srcPath, dstPath, nickname, member_setting)      # 사용자 설정 조건에 맞는 파일 이동
            break                                                           
        except:                                                             # 예외 발생시 다시 수행
            continue

    while(True):            
        try:
            guestFileRemove(srcPath, 0)                                     # 사용자 설정 조건에 해당되지 않는 파일 제거
            guestFileRemove(srcPath, 1)                                     # 사용자 설정 조건에 해당되지 않는 파일 제거
            break                                                           # 파일 제거가 성공하면 루프 종료
        except:                                                             # 예외 발생시 다시 수행
            continue

    encrypt_all_files(dstPath,nickname)                                                           # 경로에 존재하는 모든 파일 암호화
    QSystemTrayIcon.showMessage(emptyTrayicon, "알림:", "암호화가 완료되었습니다.", 1, 1000)        # 시스템 트레이 아이콘에 메시지를 1초 동안 표시 

    focusThread.terminate()                 # 스레드 종료 
    emptyTrayicon.hide()                    # 시스템 트레이 아이콘 숨김
    keyboard.unhook_all()                   # 키보드 후킹 모두 해제

# 비 로그인 상태에서 trayicon이 수행하는 메서드
def trayMem(flag, nickname, member_setting):
    check = 0                               
    srcPath = getSrcPath()                      # 소스 경로 할당
    dstPath = getDstPath(nickname)              # 목적지 경로 할당

    for proc in psutil.process_iter():          # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()                   # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":             # 현재 프로세스 이름이 "chrome.exe"인 경우
            check = 1                           # 크롬 실행 플래그 세팅
            break                           

    if(check == 0 and flag == False):                                           # 크롬이 꺼져있고 암호화를 실행하지 않은 경우
        if((int)(get_idle_duration()) >= 60):                                   # idle한 시간이 threshold 이상인 경우
            encryptInTrayIcon(srcPath, dstPath, nickname, member_setting)       # 암호화 기능 수행
            return True                                                         # 반복 실행 방지
        return False                                                            # idle한 상태가 타임아웃보다 적은 상태
    elif(check == 0 and flag == True):                                          # 크롬이 꺼지고 이미 암호화를 한 경우
        return True                                                             # 현 상태 유지
    else:                                                                   
        return False

# 메일을 전송하는 기능을 수행하는 메서드
def sendMail(address):
    code = genCode()                                # 사용자 확인 코드 생성

    MY_ADDRESS, MY_PASSWORD = getAgentEmail()       # 에이전트 이메일 정보 할당

    TO_ADDRESS = address                            # 수신자 이메일 주소 할당

    # 이메일 구성
    message = EmailMessage()                        # EmailMessage 객체 생성
    message['From'] = formataddr(('PIM AGENT', MY_ADDRESS))                                         # 발신자 이름과 이메일 주소 설정 
    message['To'] = TO_ADDRESS                                                                      # 수신자 이메일 주소 설정

    message['Subject'] = '[PIM AGENT] 비밀번호 재설정을 하기위한 메시지 입니다.'                       # 이메일 제목 설정                 

    body = '비밀번호를 재설정 하기 위해\n해당 6자리 코드({})를 입력해 주세요'.format(code)           # 이메일 내용 입력

    message.set_content(body)                                                                       # 이메일 내용을 설정

    # SMTP 설정
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:                               
        smtp.starttls()                                                             # TLS 보안 연결을 설정
        smtp.login(MY_ADDRESS, MY_PASSWORD)                                         # 이메일 계정으로 로그인
        smtp.send_message(message)                                                  # 이메일 전송

    return code                                                                     # 생성된 인증 코드를 반환
