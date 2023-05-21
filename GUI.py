import sys
import re
import os
import time
import pymysql

from tendo import singleton
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *

from Run import runMem, runGuest, trayGuest, trayMem, sendMail, encryptInTrayIcon
from RunData import initCheck, getSrcPath, getDstPath
from DB_setting import getLoginData, checkIDUnique, checkNicknameUnique, setMembership, getID, getEmail, resetPw, setCustomSetting, getCustomSetting
from LoadingGUI import preGuestClass, preMemClass, EncryptLoadingClass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))                           # 절대경로 사용을 위한 베이스 경로

init_form_class = uic.loadUiType(BASE_DIR + r'\UI\initGUI.ui')[0]               # 초기화면 ui파일을 불러옴
login_form_class = uic.loadUiType(BASE_DIR + r'\UI\loginGUI.ui')[0]             # 로그인 전 메인화면 ui파일을 불러옴
run_form_class = uic.loadUiType(BASE_DIR + r'\UI\runGUI.ui')[0]                 # 로그인 후 메인화면 ui파일를 불러옴
join_form_class = uic.loadUiType(BASE_DIR + r'\UI\joinGUI.ui')[0]               # 회원가입 화면 ui파일를 불러움
find_form_class = uic.loadUiType(BASE_DIR + r'\UI\findGUI.ui')[0]               # 회원 정보를 찾기 위한 화면 ui파일을 불러옴
validEmail_form_class = uic.loadUiType(BASE_DIR + r'\UI\validEmailGui.ui')[0]   # 이메일로 전송된 코드를 인증하기 위한 화면 ui파일을 불러옴
resetPw_form_class = uic.loadUiType(BASE_DIR + r'\UI\resetPwGui.ui')[0]         # 비밀번호를 재설정 하기위한 화면 ui파일을 불러옴


# GUI가 보이는 상태에서 로그인 전 파일 삭제기능을 위해 크롬의 on/off를 체크하는 스레드
class runGuestThread(QThread):                                                    
    timeout_signal = pyqtSignal()               # 파일 삭제 기능을 수행하는 gui를 실햏하기 위한 시그널

    # 초기화 메서드
    def __init__(self):
        super().__init__()
        self.breakPoint = False                 # run()메소드를 언제까지 실행할 지 결정
        self.flag = False                       # 파일 삭제 기능을 수행하는 gui를 실행할지 말지 결정
        self.acc = 0                            # 크롬이 켜지면 값을 누적, 꺼지면 유지
        self.var = 0                            # 현재 크롬이 켜져있으면 on, 아니면 off

    # 쓰레드로 동작시킬 함수
    def run(self):
        while(not self.breakPoint):            
            self.var, self.acc, self.flag = runGuest(self.var, self.acc)   # self.flag의 값을 결정하는 메소드 수행
            if self.flag == True:
                self.breakPoint = True
                self.quit()                     # 크롬이 켜졌다 꺼짐을 감지하고 특정 타임아웃이 지나면 스레드 종료
                self.timeout_signal.emit()      # 시그널 발생


# GUI가 보이는 상태에서 로그인 후 파일 암호화 기능을 위한 스레드
class runMemThread(QThread):                   
    encrypt_signal = pyqtSignal(bool)           # 암호화 기능을 수행하는 gui를 켜주기 위한 시그널

    # 초기화 메서드
    def __init__(self):
        super().__init__()
        self.breakPoint = False                 # run()메소드를 언제까지 실행할 지 결정
        self.flag = False                       # 암호화 기능을 수행하는 생성된 gui를 exec() 결정

    # 쓰레드로 동작시킬 함수 
    def run(self):
        while(not self.breakPoint):
            self.flag = runMem(self.flag)               # self.flag의 값을 결정하는 메소드 수행
            if self.flag == True:
                self.breakPoint = True
                self.quit()                             # 크롬이 꺼져있고 특정 타임아웃이 지나면 스레드 종료
                self.encrypt_signal.emit(self.flag)     # 시그널 발생


#트레이 아이콘 상태에서 로그인 전 파일 삭제기능을 위한 스레드
class trayGuestThread(QThread):
    # 초기화 메서드
    def __init__(self, parent=None):
        super().__init__()
        self.breakPoint = False                 # run()메소드를 언제까지 실행할 지 결정
        self.flag = False                       # 파일 삭제 기능을 수행할지 말지 결정

    # 쓰레드로 동작시킬 함수 
    def run(self):
        while(not self.breakPoint):
            self.flag = trayGuest(self.flag)    # 크롬이 꺼져있고 일정 타임아웃이 지나면 파일 삭제 기능 수행


#트레이 아이콘 상태에서 로그인 후 파일 암호화를 위한 스레드
class trayMemThread(QThread):
    encrypt_signal = pyqtSignal(bool)                   # 암호화 기능을 수행하는 gui를 켜주기 위한 시그널

    # 초기화 메서드(닉네임, 사용자 설정 변수 초기화)
    def __init__(self, nickname, member_setting, parent=None):  
        super().__init__()  
        self.breakPoint = False                         # run()메소드를 언제까지 실행할 지 결정           
        self.nickname = nickname                        # 닉네임 반영
        self.member_setting = member_setting            # 사용자 설졍 반영
        self.flag = False                               # 암호화 기능을 수행하는 생성된 gui를 exec() 할 지 결정

    def run(self):
        while(not self.breakPoint):     
            self.flag = trayMem(self.flag, self.nickname, self.member_setting)      # self.flag의 값을 결정하는 메소드 수행
                                                    
            if self.flag == True:
                self.breakPoint = True          
                self.encrypt_signal.emit(self.flag)     # 시그널 발생

# 트레이 아이콘 실행 class
class TrayIcon(QSystemTrayIcon):
    # 초기화 메서드(아이콘, 부모, 구별자, 닉네임, 사용자 설정 변수 초기화)
    def __init__(self, icon, parent, seperator, nickname, member_setting):
        self.icon = icon                                            # 아이콘 반영
        self.seperator = seperator                                  # 구별자 초기화      
        self.nickname = nickname                                    # 닉네임 반영
        self.member_setting = member_setting                        # 사용자 설정 반영
        QSystemTrayIcon.__init__(self, self.icon, parent)
        self.setToolTip("PIM agent")                                # 트레이 아이콘에 포커스를 줬을 때 보여줄 명칭 설정

        self.menu = QMenu()                                         # 매뉴바 설정
        self.showAction = self.menu.addAction('에이전트 실행')       # 에이전트 실행 메뉴 추가
        self.showAction.triggered.connect(self.showWindow)          # 실행 메뉴 클릭 시 gui를 보여주는 함수 호출

        self.logoutAction = self.menu.addAction("유저 로그아웃")     # 유저 로그아웃 실행 메뉴 추가
        self.logoutAction.triggered.connect(self.logout)            # 로그아웃 메뉴 클릭 시 로그아웃하는 함수 호출

        self.exitAction = self.menu.addAction('에이전트 종료')       # 에이전트 종료 실행 메뉴 추가
        self.exitAction.triggered.connect(self.exit)                # 종료 메뉴를 클릭 시 에이전트를 종료하는 함수 호출

        self.setContextMenu(self.menu)                              # 설정한 메뉴 트레이 아이콘에 부착

        self.logoutAction.setEnabled(False)                         # 실행 초기 로그아웃 메뉴 비활성화 

        self.disambiguateTimer = QTimer(self)                       # QTimer 객체 생성 및 초기화
        self.disambiguateTimer.setSingleShot(True)                  # QTimer를 한 번만 실행하도록 설정        
        self.activated.connect(self.onTrayIconActivated)            # activated 시그널과 onTrayIconActivated 슬롯을 연결

        if self.seperator == "guest":                               # 비회원일 경우
            self.th = trayGuestThread()                             # trayGuestThread 스레드 객체 생성
            self.th.start()                                         # 스레드 객체 실행

        else:                                                             # 회원일 경우
            self.logoutAction.setEnabled(True)                            # 로그아웃 메뉴 활성화
            self.th = trayMemThread(self.nickname, self.member_setting)   # trayMemThread 스레드 객체 생성  
            self.th.start()                                               # 스레드 객체 실행
            self.th.encrypt_signal.connect(self.autoLogout)               # 스레드 객체 내 encrypt_signal 시그널과 autoLogout 슬롯을 연결
    
    def onTrayIconActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:                              # 트레이 아이콘이 활성화 된 reason이 Trigger인 경우
            self.disambiguateTimer.start(qApp.doubleClickInterval())       # disambiguateTimer를 doubleClickInterval만큼 지연 실행
        elif reason == QSystemTrayIcon.DoubleClick:                        # 트레이 아이콘이 활성화 된 reason이 DoubleClick인 경우
            self.disambiguateTimer.stop()                                  # disambiguateTimer를 중지
            self.showAction.setDisabled(True)                              # 에이전트 실행 메뉴를 비활성화
            self.th.terminate()                                            # 스레드 종료
            self.hide()                                                    # 아이콘을 숨김

            if self.seperator == "guest":                                  # 더블클릭을 했을 때 비 회원일 경우
                preGuest = LoginClass(self)                                # 비 회원 gui 객체 생성
                preGuest.exec()                                            # 생성된 생성된 gui를 exec()

            else:                                                          # 더블클릭을 했을 때 회원일 경우
                mainWindow = RunClass(self)                                # 회원 gui 객체 생성
                mainWindow.setValue(self.nickname, self.member_setting)    # 회원 닉네임, 사용자 설정값을 설정
                mainWindow.setThread()                                     # runMemThread 스레드를 실행하는 함수를 호출
                mainWindow.exec()                                          # 생성된 생성된 gui를 exec() 

    # 트레이아이콘에서 gui로 전환을 위한 메서드
    def showWindow(self):                                                                            
        self.hide()                                                     # 트레이아이콘 종료
        if self.seperator == "guest":                                   # 비 회원인 경우
            preGuest = LoginClass(self)                                 # 비 회원 gui 객체 생성
            preGuest.exec()                                             # 생성된 생성된 gui를 exec()

        else:                                                           # 회원인 경우
            mainWindow = RunClass(self)                                 # 회원 gui 객체 생성
            mainWindow.setValue(self.nickname, self.member_setting)     # 회원 닉네임, 사용자 설정값을 설정
            mainWindow.setThread()                                      # runMemThread 스레드를 실행하는 함수를 호출
            mainWindow.exec()                                           # 생성된 생성된 gui를 exec() 

    # 구별자를 설정하기 위한 메서드
    def setSeperator(self, seperator):  
        self.seperator = seperator

    # 로그아웃을 위한 메서드
    def logout(self):
        os.system('taskkill /f /im chrome.exe')                         # 크롬 프로세스 종료

        self.th.terminate()                                             # 스레드 종료
        self.setSeperator("guest")                                      # 비회원으로 구별자 설정
        self.logoutAction.setEnabled(False)                             # 로그아웃 메뉴 비활성화

        encryptInTrayIcon(getSrcPath(), getDstPath(self.nickname),      # 암호화 기능을 수행하는 사용자 메서드 호출
                        self.nickname, self.member_setting)  
        
        self.th = trayGuestThread()                                     # trayGuestThread 스레드 객체 생성
        self.th.start()                                                 # 스레드 실행

    # 타임아웃에 의한 자동 로그아웃을 위한 메서드
    def autoLogout(self):                                               
        self.th.terminate()                                             # 스레드 종료             
        self.setSeperator("guest")                                      # 비회원으로 구별자 설정
        self.logoutAction.setEnabled(False)                             # 로그아웃 메뉴 비활성화

        self.th = trayGuestThread()                                     # trayGuestThread 스레드 객체 생성
        self.th.start()                                                 # 스레드 실행

    # 에이전트를 종료하기 위한 메서드
    def exit(self):
        if self.seperator == "guest":                                   # 비 회원인 경우
            self.setVisible(False)                                      # 아이콘을 숨김
            QCoreApplication.instance().quit()                          # 에이전트를 종료하는 메서드 호출

        else:                                                           # 회원일 경우
            self.setVisible(False)                                      # 크롬 프로세스 종료 
            os.system('taskkill /f /im chrome.exe')

            self.th.terminate()                                             # 스레드 종료
            encryptInTrayIcon(getSrcPath(), getDstPath(self.nickname),      # 암호화 기능을 수행하는 사용자 메서드 호출
                                    self.nickname, self.member_setting)
            QCoreApplication.instance().quit()                              # 에이전트를 종료하는 메서드 호출

# 초기 로고를 보여주는 class
class initClass(QDialog, init_form_class):
    # 초기화 메서드
    def __init__(self, app):
        super().__init__()
        self.setupUi(self)                                                       # UI 설정 메서드 호출
        self.app = app                                                           # 인스턴스 변수 app 초기화
        self.logolabel: QLabel                                                   # logolabel 변수 선언 
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))           # 윈도우 아이콘 설정
        self.setCenter()                                                         # 윈도우를 화면 중앙에 배치하는 메서드 호출
        self.prevPos = self.pos()                                                # 이전 위치 저장 변수 초기화

        self.logolabel.setPixmap(QPixmap(BASE_DIR + r"\Image\initLogo.png"))     # logolabel에 이미지 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)    # 윈도우 플래그 설정 (기본 프레임 없이, 가장 위에 올라오게)
        self.setAttribute(Qt.WA_TranslucentBackground)                           # 로고 부분만 gui에 보여지게 설정
        QTimer.singleShot(2500, self.endTitle)                                   # 타이머를 설정하고, 타이머가 타임아웃되면 endTitle 메소드 호출

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                                                # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()                       # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                                        # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                                  # 윈도우를 새로운 위치로 이동

    # gui 종료 메서드
    def endTitle(self):                                                          
        self.close()                                                             # 현재 윈도우 종료
        preGuest = LoginClass(app)                                               # 비 회원 gui 객체 생성
        preGuest.exec()                                                          # 생성된 생성된 gui를 exec()

# 비 로그인 메인화면 class
class LoginClass(QDialog, login_form_class):

    # 초기화 메서드
    def __init__(self, app):
        super().__init__()                              
        self.setupUi(self)                                                       # UI 설정 메서드 호출
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))           # 윈도우 아이콘을 지정한 아이콘으로 설정
        self.app = app                                                           # 인스턴스 변수 app 초기화

        self.srcPath = getSrcPath()                                              # 크롬에서 지정한 개인정보 폴더 경로 할당
        self.setCenter()                                                         # 윈도우를 화면 중앙에 배치하는 메서드 호출
        self.prevPos = self.pos()                                                # 이전 위치 저장 변수 할당

        self.id = ""                                                             # 아이디 필드 초기화
        self.password = ""                                                       # 패스워드 필드 초기화
        self.nickname = ""                                                       # 닉네임 필드 초기화

        self.idEdit: QLineEdit                                                   # 아이디 필드
        self.pwdEdit: QLineEdit                                                  # 패스워드 필드
        self.loginBtn: QPushButton                                               # 로그인 버튼
        self.joinBtn: QPushButton                                                # 회원가입 버튼
        self.findBtn: QPushButton                                                # id/pw 찾기 버튼
        self.runBackgroundBtn: QPushButton                                       # 백그라운드 전환 버튼
        self.minimizeBtn: QPushButton                                            # 화면 최소화 버튼
        self.iconlabel: QLabel                                                   # 아이콘 레이블

        self.setWindowFlags(Qt.FramelessWindowHint)                              # 기본 프레임 없이 설정

        self.runBackgroundBtn.setIcon( QIcon(BASE_DIR + r"\Image\closeIcon.png"))       # 백그라운드 버튼에 종료버튼 아이콘 적용
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))          # 최소화 버튼에 최소화 아이콘 적용
        self.iconlabel.setPixmap(                                                       # 아이콘 레이블에 로고 아이콘 적용
                QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.daemonThread = runGuestThread()                                   # runGuestThread 스레드 객체 생성
        self.daemonThread.timeout_signal.connect(self.loading)                 # 스레드 객체 내 timeout_signal 시그널과 loading 슬롯 연결
        self.daemonThread.start()                                              # 스레드 실행

        self.loginBtn.clicked.connect(self.btnLoginFunc)              # 로그인 버튼 클릭 시그널과 btnLoginFunc 메서드 연결          
        self.joinBtn.clicked.connect(self.btnJoinFunc)                # 회원가입 버튼 클릭 시그널과 btnJoinFunc 메서드 연결
        self.findBtn.clicked.connect(self.btnFindFunc)                # id/pw찾기 버튼 클릭 시그널과 btnFindFunc 메서드 연결
        self.minimizeBtn.clicked.connect(self.minimize)               # 최소화 버튼 클릭 시그널과 minimize 메서드 연결
        self.runBackgroundBtn.clicked.connect(self.runBackground)     # 백그라운드 버튼 클릭 시그널과 runBackground 메서드 연결

        initCheck()             # 개인정보 파일을 담을 루트 폴더를 지정 경로에 생성

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                              # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()     # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                      # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                # 윈도우를 새로운 위치로 이동

    # 마우스 클릭 이벤트 처리 메서드
    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()    # 현재 마우스 위치를 저장

    # 마우스 이동 이벤트 처리 메서드
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)        # 이동한 거리 계산
        self.move(self.x() + delta.x(), self.y() + delta.y())   # 윈도우를 이동한 거리만큼 이동
        self.prevPos = event.globalPos()                        # 현재 마우스 위치를 업데이트

    def loading(self):
        self.close()                                    # 현재 윈도우 종료

        preGuestclass = preGuestClass(self.srcPath)     # 파일 삭제 gui 객체 생성
        preGuestclass.exec()                            # 생성된 gui를 exec()

        preGuest = LoginClass(self.app)                 # 비 회원 gui 객체 생성
        preGuest.exec()                                 # 생성된 gui를 exec()

    # 최소화 메서드
    def minimize(self):
        self.showMinimized()        # 윈도우를 최소화

    # 백그라운드 실행 메서드
    def runBackground(self):                                                               
        self.daemonThread.terminate()                                                       # 현재 실행되는 스레드 종료 
        self.hide()                                                                         # 윈도우 숨기기

        trayicon = TrayIcon(                                                                # TrayIcon 객체 생성
            QIcon(BASE_DIR + r'\Image\windowIcon.png'), self.app, "guest", "guest", None)   
        trayicon.setVisible(True)                                                           # TrayIcon 표시 설정
        trayicon.show()                                                                     # TrayIcon 출력

    # 로그인 버튼 메서드
    def btnLoginFunc(self):
        self.id = self.idEdit.text()            # 입력된 아이디 가져오기
        self.password = self.pwdEdit.text()     # 입력된 패스워드 가져오기

        if not(self.idEdit.text() and self.pwdEdit.text()):                                 # 아이디 또는 비밀번호가 비어있는 경우
            QMessageBox.setStyleSheet(                                                      # 메시지 박스 스타일 시트 설정
                self, 'QMessageBox {color: rgb(120, 120, 120)}')
            QMessageBox.information(                                                        # 입력 요청 메시지 박스 표시
                self, 'PIM agent', "아이디 또는 비밀번호를 입력해 주세요.", QMessageBox.Yes)
            return

        try:
            checkLogin, self.nickname = getLoginData(self.id, self.password)        # 로그인 데이터 확인
            member_setting = getCustomSetting(self.nickname)                        # 사용자 설정 정보 가져오기

            if(checkLogin):                                                     # 로그인 성공한 경우
                self.close()                                                    # 현재 윈도우 종료
                self.daemonThread.terminate()                                   # runGuestThread 스레드 종료

                preMemThread = preMemClass(self.nickname, member_setting)       # preMemClass 객체 생성
                preMemThread.exec()                                             # 생성된 gui를 exec() 

                mainWindow = RunClass(self.app)                                 # RunClass 객체 생성          
                mainWindow.setValue(self.nickname, member_setting)              # 닉네임과 사용자 설정 전달
                mainWindow.setThread()                                          # runMemThread 스레드를 실행하는 메서드 호출

                mainWindow.exec()                                               # 생성된 gui를 exec() 
        except Exception as e:              # 발생한 예외를 e 객체로 예외처리 수행
            if str(e) == '(2003, \"Can\'t connect to MySQL server on \'3.39.9.144\' (timed out)\")':    # MySQL 서버 연결 오류인 경우
                QMessageBox.setStyleSheet(                                                              # 메시지 박스 스타일 시트 설정
                    self, 'QMessageBox {color: rgb(120, 120, 120)}')    
                QMessageBox.information(                                                                # 메시지 박스 표시
                    self, 'PIM agent', "원격 네트워크 환경을 확인해주세요.", QMessageBox.Yes)
            elif str(e) == 'tuple index out of range':                                                  # 회원 정보와 일치하는 계정이 없는 경우                 
                QMessageBox.setStyleSheet(                                                              # 메시지 박스 스타일 시트 설정
                    self, 'QMessageBox {color: rgb(120, 120, 120)}')
                QMessageBox.information(                                                                # 메시지 박스 표시
                    self, 'PIM agent', "입력하신 회원 정보와 일치하는 계정이 없습니다.", QMessageBox.Yes) 
            else:                                                                                       # 그 외의 네트워크 오류인 경우
                QMessageBox.setStyleSheet(
                    self, 'QMessageBox {color: rgb(120, 120, 120)}')                                    # 메시지 박스 스타일 시트 설정
                QMessageBox.information(
                    self, 'PIM agent', "로컬 네트워크 환경을 확인해주세요.", QMessageBox.Yes)              # 메시지 박스 표시
    
    # 가입 버튼 메서드
    def btnJoinFunc(self):
        self.setCenter()                # 윈도우를 화면 중앙에 배치
        self.daemonThread.terminate()   # runGuestThread 스레드 종료

        joinWindow = JoinClass()        # JoinClass 객체 생성
        joinWindow.exec()               # 생성된 gui를 exec()

        self.daemonThread.start()       # JoinClass gui 종료 시 runGuestThread 스레드 실행

    # ID 찾기/PW 재설정 버튼 메서드
    def btnFindFunc(self):
        self.setCenter()                    # 윈도우를 화면 중앙에 배치
        self.daemonThread.terminate()       # runGuestThread 스레드 종료

        findWindow = FindClass()            # FindClass 객체 생성
        findWindow.exec()                   # 생성된 gui를 exec()

        self.daemonThread.start()           # FindClass gui 종료 시 runGuestThread 스레드 실행

# 로그인 메인화면 class
class RunClass(QDialog, run_form_class):
    # 초기화 메서드
    def __init__(self, app):
        super().__init__()
        self.setupUi(self)                                                  # UI 설정 메서드 호출
        self.app = app                                                      # 인스턴스 변수 app 초기화
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))      # 윈도우 아이콘을 지정한 아이콘으로 설정

        self.setCenter()                # 윈도우를 화면 중앙에 배치하는 메서드 호출 
        self.prevPos = self.pos()       # 이전 위치 저장 변수 초기화

        self.nickname = ""              # 초기 닉네임 초기화
        self.member_setting = None      # 초기 사용자 설정 초기화

        self.titleLabel: QLabel         # 닉네임 레이블
        self.iconlabel: QLabel          # 아이콘 표시 레이블 

        self.bookmarkCheckBox: QCheckBox        # 북마크 체크박스
        self.visitCheckBox: QCheckBox           # 방문기록 체크박스
        self.downloadCheckBox: QCheckBox        # 다운로드기록 체크박스
        self.autoFormCheckBox: QCheckBox        # 자동완성양식 체크박스
        self.cookieCheckBox: QCheckBox          # 쿠키파일 체크박스
        self.cacheCheckBox: QCheckBox           # 캐시파일 체크박스
        self.sessionCheckBox: QCheckBox         # 세션파일 체크박스

        self.setDBBtn: QPushButton              # 사용자 설정 버튼 
        self.logoutBtn: QPushButton             # 로그아웃 버튼
        self.runBackgroundBtn: QPushButton      # 백그라운드 실행 버튼
        self.minimizeBtn: QPushButton           # 윈도우 최소화 버튼

        self.iconlabel.setPixmap(                                                   # 아이콘 표시 레이블에 아이콘 이미지 삽입
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))
        self.runBackgroundBtn.setIcon(                                              # 백그라운드 실행 버튼에 아이콘 이미지 삽입
            QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))      # 윈도우 최소화 버튼에 아이콘 이미지 삽입

        self.titleLabel.setAlignment(Qt.AlignCenter)            # 닉네임표시 레이블 가운데 정렬
        self.setWindowFlags(Qt.FramelessWindowHint)             # 기본 프레임 없이 설정

        self.setDBBtn.clicked.connect(self.setDB)                       # 사용자 설정 버튼 클릭 시그널과 setDB 메서드 연결
        self.logoutBtn.clicked.connect(self.logout)                     # 로그아웃 버튼 클릭 시그널과 logout 메서드 연결
        self.minimizeBtn.clicked.connect(self.minimize)                 # 윈도우 최소화 버튼 클릭 시그널과 minimize 메서드 연결  
        self.runBackgroundBtn.clicked.connect(self.runBackground)       # 백그라운드 실행 버튼 클릭 시그널과 runBackground 메서드 연결

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                              # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()     # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                      # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                # 윈도우를 새로운 위치로 이동

    # 마우스 클릭 이벤트 처리 메서드
    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()    # 현재 마우스 위치를 저장

    # 마우스 이동 이벤트 처리 메서드
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)        # 이동한 거리 계산
        self.move(self.x() + delta.x(), self.y() + delta.y())   # 윈도우를 이동한 거리만큼 이동
        self.prevPos = event.globalPos()                        # 현재 마우스 위치를 업데이트

    # 닉네임, 사용자 설정 할당 메서드
    def setValue(self, nickname, member_setting):
        self.nickname = nickname
        self.member_setting = member_setting

        self.titleLabel.setText(nickname + " 님")           # 메인화면 상단에 사용자 닉네임 출력

        if member_setting[0] == 0:                          # 사용자 북마크 체크박스 토글 설정
            self.bookmarkCheckBox.toggle()                  
        if member_setting[1] == 0:                          # 사용자 방문기록 체크박스 토글 설정
            self.visitCheckBox.toggle()                     
        if member_setting[2] == 0:                          # 사용자 다운로드기록 체크박스 토글 설정
            self.downloadCheckBox.toggle()                  
        if member_setting[3] == 0:                          # 사용자 자동완성양식 체크박스 토글 설정
            self.autoFormCheckBox.toggle()                  
        if member_setting[4] == 0:                          # 사용자 쿠키파일 체크박스 토글 설정
            self.cookieCheckBox.toggle()                    
        if member_setting[5] == 0:                          # 사용자 캐시파일 체크박스 토글 설정
            self.cacheCheckBox.toggle()                     
        if member_setting[6] == 0:                          # 사용자 세션파일 체크박스 토글 설정
            self.sessionCheckBox.toggle()                   

    # runMemThread 스레드를 실행하고 시그널, 슬롯을 연결하는 메서드
    def setThread(self):
        self.daemonThread = runMemThread()                          # runMemThread 스레드 객체 생성
        self.daemonThread.start()                                   # 스레드 실행
        self.daemonThread.encrypt_signal.connect(self.logout)       # 스레드 내 encrypt_signal 시그널과 logout 슬롯 연결

    # 사용자 옵션 설정 메서드
    def setDB(self):
        bookmarkCheck = 1 if self.bookmarkCheckBox.isChecked() is True else 0       # 사용자 북마크 관리 선택/취소 여부 확인
        visitCheck = 1 if self.visitCheckBox.isChecked() is True else 0             # 사용자 방문기록 관리 선택/취소 여부 확인
        downloadCheck = 1 if self.downloadCheckBox.isChecked() is True else 0       # 사용자 다운로드기록 관리 선택/취소 여부 확인
        autoFormCheck = 1 if self.autoFormCheckBox.isChecked() is True else 0       # 사용자 자동완성양식 관리 선택/취소 여부 확인
        cookieCheck = 1 if self.cookieCheckBox.isChecked() is True else 0           # 사용자 쿠키파일 관리 선택/취소 여부 확인
        cacheCheck = 1 if self.cacheCheckBox.isChecked() is True else 0             # 사용자 캐시파일 관리 선택/취소 여부 확인
        sessionCheck = 1 if self.sessionCheckBox.isChecked() is True else 0         # 사용자 세션파일 관리 선택/취소 여부 확인

        try:                                                                            
            setCustomSetting(bookmarkCheck, visitCheck, downloadCheck, autoFormCheck,       # 사용자 옵션을 데이터베이스에 업데이트
                            cookieCheck, cacheCheck, sessionCheck, self.nickname)
        
        except pymysql.err.OperationalError:                                        # 데이터 베이스 예외 발생                          
            QMessageBox.information(                                                # 메시지 박스 출력
                self, 'PIM agent', "요청이 너무 많아 응답이 지연되고 있습니다.\n잠시 후 다시 시도바랍니다.", QMessageBox.Yes)
            pass

        self.member_setting = (bookmarkCheck, visitCheck, downloadCheck,            # 사용자 설정 저장
                            autoFormCheck, cookieCheck, cacheCheck, sessionCheck)

        self.daemonThread.terminate()                                               # runGuestThread 스레드 종료
        self.daemonThread = runMemThread()                                          # runMemThread 스레드 객체 생성
        self.daemonThread.start()                                                   # 스레드 실행
        self.daemonThread.encrypt_signal.connect(self.logout)                       # 스레드 내 encrypt_signal 시그널과 logout 슬롯 연결

        QMessageBox.setStyleSheet(                                                  # 메시지 박스 스타일 시트 설정
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        QMessageBox.information(                                                    # 메시지 박스 표시
            self, 'PIM agent', "사용자 설정이 완료되었습니다.", QMessageBox.Yes)

    # 최소화 메서드
    def minimize(self):
        self.showMinimized()    # 윈도우 최소화

    def runBackground(self):    
        self.hide()                                                                     # 윈도우 숨기기
        self.daemonThread.terminate()                                                   # 현재 실행되는 스레드 종료
        
        trayicon = TrayIcon(QIcon(BASE_DIR + r'\Image\windowIcon.png'), \
                            self.app, "member", self.nickname, self.member_setting)     # TrayIcon 객체 생성
        trayicon.show()                                                                 # TrayIcon 출력

    # 로그아웃 메서드
    def logout(self):
        self.daemonThread.terminate()                                                   # 현재 실행되는 스레드 종료
        self.close()                                                                    # 실행 중인 gui 종료

        os.system('taskkill /f /im chrome.exe')                                         # 크롬 프로세스 종료

        encryptThread = EncryptLoadingClass(getSrcPath(), getDstPath(self.nickname)     # 암호화 기능 gui 객체 생성
                                            ,self.nickname, self.member_setting)
        encryptThread.exec()                                                            # 암호화 기능 gui exec()

        preGuest = LoginClass(self.app)                                                 # 비 로그인 gui 객체 생성
        preGuest.exec()                                                                 # 비 로그인 gui exec()


# 회원가입 gui를 보여주는 class
class JoinClass(QDialog, join_form_class):
    
    # 초기화 메서드
    def __init__(self):
        super().__init__()
        self.setupUi(self)                  # UI 설정 메서드 호출

        self.setCenter()                    # 윈도우를 화면 중앙에 배치하는 메서드 호출 
        self.prevPos = self.pos()           # 이전 위치 저장 변수 초기화

        self.idEdit: QLineEdit              # 아이디 필드
        self.pwdEdit: QLineEdit             # 패스워드 필드
        self.emailEdit: QLineEdit           # 이메일 필드
        self.nicknameEdit: QLineEdit        # 닉네임 필드
        self.joinBtn: QPushButton           # 회원가입 버튼
        self.gotoMainBtn: QPushButton       # 윈도우 종료 버튼 (메인으로 돌아가기 버튼)
        self.closeBtn: QPushButton          # 윈도우 종료 버튼 (상단 종료 버튼)
        self.minimizeBtn: QPushButton       # 윈도우 최소화 버튼
        self.iconlabel: QLabel              # 아이콘 레이블

        self.idEdit.setText("")             # 아이디 필드 초기화
        self.pwdEdit.setText("")            # 비밀번호 필드 초기화
        self.emailEdit.setText("")          # 이메일 필드 초기화
        self.nicknameEdit.setText("")       # 닉네임 필드 초기화

        self.setWindowFlags(Qt.FramelessWindowHint)                                 # 기본 프레임 없이 설정
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))              # 윈도우 아이콘을 지정한 아이콘으로 설정

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))            # 윈도우 종료 버튼에 아이콘 이미지 삽입
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))      # 윈도우 최소화 버튼에 아이콘 이미지 삽입
        self.iconlabel.setPixmap(                                                   # 아이콘 레이블에 아이콘 이미지 삽입
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.joinBtn.clicked.connect(self.join)                           # 회원가입 버튼 클릭 시그널과 join 메서드 연결
        self.closeBtn.clicked.connect(self.gotoMain)                      # 윈도우 종료 버튼(메인으로 돌아가기 버튼) 클릭 시그널과 gotoMain 메서드 연결
        self.gotoMainBtn.clicked.connect(self.gotoMain)                   # 윈도우 종료 버튼(상단 종료 버튼) 클릭 시그널과 gotoMain 메서드 연결
        self.minimizeBtn.clicked.connect(self.minimize)                   # 윈도우 최소화 버튼 클릭 시그널과 minimize 메서드 연결

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                              # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()     # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                      # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                # 윈도우를 새로운 위치로 이동

    # 마우스 클릭 이벤트 처리 메서드
    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()    # 현재 마우스 위치를 저장

    # 마우스 이동 이벤트 처리 메서드
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)        # 이동한 거리 계산
        self.move(self.x() + delta.x(), self.y() + delta.y())   # 윈도우를 이동한 거리만큼 이동
        self.prevPos = event.globalPos()                        # 현재 마우스 위치를 업데이트

    # 회원가입 아이디 규칙(6자리 이상 12자리 이하,하나 이상의 영문과 숫자로 구성)매칭 메서드
    def checkIDValid(self, edit):
        if re.search('^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,12}$', edit) is None:
            return False
        else:
            return True
        
    # 회원가입 비밀번호 규칙(8자리 이상,하나 이상의 영문,숫자,특수문자로 구성)매칭 메서드
    def checkPWValid(self, edit):
        if re.search('^(?=.*[A-Za-z])(?=.*\d)(?=.*[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"])[A-Za-z\d\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]{8,}$', edit) is None:
            return False
        else:
            return True
        
    # 회원가입 이메일 규칙 매칭 메서드
    def emailValid(self, edit):
        if re.search('^[a-zA-Z0-9._-]+@[a-zA-Z0-9.]+\.[a-zA-Z]{2,4}$', edit) is None:
            return False
        else:
            return True
        
    # 회원가입 닉네임 규칙(16자리 이하,공백 포함불가) 매칭 메서드
    def nicknameValid(self, nickname):
        if re.search('^(?!.*\s)(?=.*[a-zA-Z0-9ㄱ-ㅎ가-힣]).{0,16}$', nickname) is None:
            return False
        else:
            return True

    # 회원가입 메서드
    def join(self):
        QMessageBox.setStyleSheet(                                                  # 메시지 박스 스타일 시트 설정
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        
        idValidation = self.checkIDValid(self.idEdit.text())                        # 아이디 매칭 결과 유효성 확인
        pwdValidation = self.checkPWValid(self.pwdEdit.text())                      # 패스워드 매칭 결과 유효성 확인
        emailValidation = self.emailValid(self.emailEdit.text())                    # 이메일 매칭 결과 유효성 확인
        nicknameValidation = self.nicknameValid(self.nicknameEdit.text())           # 닉네임 매칭 결과 유효성 확인

        if not(self.idEdit.text() and self.pwdEdit.text() and 
                self.emailEdit.text() and self.nicknameEdit.text()):                                # 입력하지 않은 정보가 존재할 경우
            QMessageBox.information(
                self, 'PIM agent', "입력하지 않은 정보가 있습니다.", QMessageBox.Yes)
        elif not idValidation:                                                                      # ID가 회원가입 규칙에 맞지 않는 경우
            QMessageBox.information(
                self, 'PIM agent', "입력한 ID가 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not pwdValidation:                                                                     # PW가 회원가입 규칙에 맞지 않는 경우
            QMessageBox.information(
                self, 'PIM agent', "입력한 PW가 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not emailValidation:                                                                   # 이메일 형식이 잘못된 경우
            QMessageBox.information(
                self, 'PIM agent', "이메일 형식이 잘못되었습니다.", QMessageBox.Yes)
        elif not nicknameValidation:                                                                # 닉네임이 회원가입 규칙에 맞지 않는 경우
            QMessageBox.information(
                self, 'PIM agent', "입력한 닉네임이 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not checkIDUnique(self.idEdit.text()):                                                 # 이미 존재하는 ID인 경우
            QMessageBox.information(
                self, 'PIM agent', "입력한 ID가 이미 존재합니다.", QMessageBox.Yes)
        elif not checkNicknameUnique(self.nicknameEdit.text()):                                     # 이미 존재하는 닉네임인 경우
            QMessageBox.information(
                self, 'PIM agent', "입력한 닉네임이 이미 존재합니다.", QMessageBox.Yes)
        else:                                                                                       # 모든 조건을 만족한 경우
            setMembership(self.idEdit.text(), self.pwdEdit.text(),                              
                            self.emailEdit.text(), self.nicknameEdit.text())                        # 데이터 베이스 계정 업데이트
            QMessageBox.information(
                self, 'PIM agent', "회원가입에 성공하였습니다.", QMessageBox.Yes)
            self.close()                                                                            # 회원가입 gui 종료        

    # 최소화 메서드
    def minimize(self):
        self.showMinimized()    # 윈도우 최소화

    # 윈도우 종료 메서드
    def gotoMain(self):
        self.close()            # 윈도우 종료

# ID 찾기/ PW 재설정 화면 class
class FindClass(QDialog, find_form_class):
    # 초기화 메서드
    def __init__(self):
        super().__init__()
        self.setupUi(self)                          # UI 설정 메서드 호출

        self.setCenter()                            # 윈도우를 화면 중앙에 배치하는 메서드 호출
        self.prevPos = self.pos()                   # 이전 위치 저장 변수 초기화       

        self.findIdFromNicknameEdit: QLineEdit      # 아이디를 찾기위한 닉네임 입력 필드
        self.resPwFromIDEdit: QLineEdit             # 비밀번호 재설정을 위한 아이디 필드
        self.resPwFromNicknameEdit: QLineEdit       # 비밀번호 재설정을 위한 닉네임 입력 필드

        self.findIDBtn: QPushButton                 # 아이디 찾기 버튼
        self.resPWBtn: QPushButton                  # 비밀번호 재설정 버튼
        self.gotoMainBtn: QPushButton               # 윈도우 종료 버튼(메인으로 돌아가기 버튼)
        self.iconlabel: QLabel                      # 아이콘 레이블
        self.closeBtn: QPushButton                  # 윈도우 종료 버튼(상단 종료 버튼)
        self.minimizeBtn: QPushButton               # 윈도우 최소화 버튼

        self.setWindowFlags(Qt.FramelessWindowHint)                                 # 기본 프레임 없이 설정
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))              # 윈도우 아이콘을 지정한 아이콘으로 설정

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))            # 윈도우 종료 버튼에 아이콘 이미지 삽입
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))      # 윈도우 최소화 버튼에 아이콘 이미지 삽입
        self.iconlabel.setPixmap(                                                   # 아이콘 레이블에 아이콘 이미지 삽입
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.findIDBtn.clicked.connect(self.findIDFunc)         # 아이디 찾기 버튼 클릭 시그널과 findIDFunc 메서드 연결
        self.resPWBtn.clicked.connect(self.resetPWFunc)         # 비밀번호 재설정 버튼 클릭 시그널과 resetPWFunc 메서드 연결
        self.closeBtn.clicked.connect(self.gotoMain)            # 윈도우 종료 버튼(메인으로 돌아가기 버튼) 클릭 시그널과 gotoMain 메서드 연결 
        self.minimizeBtn.clicked.connect(self.minimize)         # 윈도우 최소화 버튼 클릭 시그널과 minimize 메서드 연결
        self.gotoMainBtn.clicked.connect(self.gotoMain)         # 윈도우 종료 버튼(상단 종료 버튼) 클릭 시그널과 gotoMain 메서드 연결

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                              # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()     # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                      # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                # 윈도우를 새로운 위치로 이동

    # 마우스 클릭 이벤트 처리 메서드
    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()    # 현재 마우스 위치를 저장

    # 마우스 이동 이벤트 처리 메서드
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)        # 이동한 거리 계산
        self.move(self.x() + delta.x(), self.y() + delta.y())   # 윈도우를 이동한 거리만큼 이동
        self.prevPos = event.globalPos()                        # 현재 마우스 위치를 업데이트

    # 아이디 찾기 메서드
    def findIDFunc(self):                   
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')                        # 메시지 박스 스타일 시트 설정
        
        if not self.findIdFromNicknameEdit.text():                                  # 닉네임이 입력되지 않은 경우
            QMessageBox.information(
                self, 'PIM agent', "닉네임이 입력되지 않았습니다.", QMessageBox.Yes)
        else:
            result, resultID = getID(self.findIdFromNicknameEdit.text())            # 데이터베이스 조회를 통해 조건에 맞는 아이디 추출

            if(result):                                                             # 조회에 성공한 경우
                QMessageBox.information(
                    self, 'PIM agent', "해당 닉네임으로 연결된 ID는 " + resultID[:-3] + "***" + " 입니다.", QMessageBox.Yes)
                self.close()
            else:                                                                   # 조회에 실패한 경우
                QMessageBox.information(                        
                    self, 'PIM agent', "해당 닉네임으로 연결된 ID는 없습니다.", QMessageBox.Yes)
                
    #비밀번호 재설정 메서드
    def resetPWFunc(self):
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')                                # 메시지 박스 스타일 시트 설정
        
        if not(self.resPwFromIDEdit.text() and self.resPwFromNicknameEdit.text()):          # 정보가 입력되지 않은 경우
            QMessageBox.information(
                self, 'PIM agent', "ID나 닉네임이 입력되지 않았습니다.", QMessageBox.Yes)
        else:                                                                               
            result, resultEmail = getEmail(                                                 
                self.resPwFromIDEdit.text(), self.resPwFromNicknameEdit.text())             # 데이터베이스를 조회해 조건에 맞는 이메일 추출

            if(result):                                                                                     # 조회에 성공한 경우
                self.code = sendMail(resultEmail)                                                           # 사용자 확인 메일 전송
                self.close()                                                                                # 윈도우 종료
                validCodeClass = ValidCodeClass(resultEmail, self.resPwFromNicknameEdit.text(), self.code)  # ValidCodeClass 객체 생성
                validCodeClass.exec()                                                                       # 생성된 gui를 exec() 
            else:                                                                                           # 조회에 실패한 경우
                QMessageBox.information(
                    self, 'PIM agent', "해당 ID와 닉네임으로 연결된 PW는 없습니다.", QMessageBox.Yes)
            self.close()                                                                                    # 윈도우 종료

    # 최소화 메서드
    def minimize(self):
        self.showMinimized()    # 윈도우 최소화

    # 윈도우 종료 메서드
    def gotoMain(self):
        self.close()            # 윈도우 종료

# 이메일로 전송된 인증번호를 확인하는 class
class ValidCodeClass(QDialog, validEmail_form_class):
    # 초기화 메서드
    def __init__(self, email, nickname, code):
        super().__init__()
        self.setupUi(self)              # UI 설정 메서드 호출
        self.code = code                # 인증코드 초기화

        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))          # 윈도우 아이콘을 지정한 아이콘으로 설정      
        self.email = email                                                      # 이메일 초기화
        self.send_time = time.time()                                            # 코드 유효성 확인을 위해 현재 시간 측정
        self.nickname = nickname                                                # 닉네임 초기화

        self.setCenter()                                                        # 윈도우를 화면 중앙에 배치하는 메서드 호출 
        self.prevPos = self.pos()                                               # 이전 위치 저장 변수 초기화

        self.validBtn: QPushButton                                              # 인증 버튼
        self.resendBtn: QPushButton                                             # 재전송 버튼
        self.closeBtn: QPushButton                                              # 윈도우 종료 버튼
        self.minimizeBtn: QPushButton                                           # 윈도우 최소화 버튼

        self.iconlabel: QLabel                                                  # 아이콘 레이블
        self.codeEdit: QLineEdit                                                # 코드 입력 필드

        self.codeEdit.setText("")                                               # 초기 코드 입력 필드 초기화

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))        # 윈도우 끄기 버튼에 아이콘 이미지 삽입
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))  # 윈도우 최소화 버튼에 아이콘 이미지 삽입
        self.iconlabel.setPixmap(                                               # 아이콘 레이블에 아이콘 이미지 삽입
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.validBtn.clicked.connect(self.validFunc)                           # 인증 버튼 클릭 시그널과 validFunc 메서드 연결
        self.resendBtn.clicked.connect(self.resendFunc)                         # 재전송 버튼 클릭 시그널과 resendFunc 메서드 연결
        self.closeBtn.clicked.connect(self.gotoMain)                            # 윈도우 종료 버튼 클릭 시그널과 gotoMain 메서드 연결
        self.minimizeBtn.clicked.connect(self.minimize)                         # 윈도우 최소화 버튼 클릭 시그널과 minimize 메서드 연결

        self.setWindowFlags(Qt.FramelessWindowHint)                             # 기본 프레임 없이 설정

    # 최소화 메서드
    def minimize(self):
        self.showMinimized()    # 윈도우 최소화

    # 윈도우 종료 메서드
    def gotoMain(self):
        self.close()            # 윈도우 종료

    # 인증코드 확인 메서드
    def validFunc(self):
        if not self.codeEdit.text():                                                            # 인증코드가 비었을 경우
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')                                # 메시지 박스 스타일 시트 설정
            QMessageBox.information(
                self, 'PIM agent', "인증코드가 입력되지 않았습니다.", QMessageBox.Yes)
        elif time.time() - self.send_time > 600:                                                # 인증코드가 만료되었을 경우
            QMessageBox.information(
                self, 'PIM agent', "인증코드가 만료되었습니다. 재시도 바랍니다.", QMessageBox.Yes)
        elif self.codeEdit.text() == self.code:                                                 # 전송한 인증코드와 일치할 경우
            self.close()                                                                        # 윈도우 종료
            resetPw = resetPwClass(self.nickname)                                               # resetPwClass gui객체 생성
            resetPw.exec()                                                                      # 생성된 gui를 exec() 
        else:                                                                                   # 전송한 인증코드와 일치하지 않을 경우
            QMessageBox.information(
                self, 'PIM agent', "인증코드가 일치하지 않습니다.", QMessageBox.Yes)
            
    # 인증코드 재전송 메서드
    def resendFunc(self):
        self.send_time = time.time()                                            # 전송시간 초기화
        self.code = sendMail(self.email)                                        # 인증코드 재전송
        QMessageBox.setStyleSheet(  
            self, 'QMessageBox {color: rgb(120, 120, 120)}')                    # 메시지 박스 스타일 시트 설정
        QMessageBox.information(
            self, 'PIM agent', "인증코드를 재전송 하였습니다.", QMessageBox.Yes)

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                              # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()     # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                      # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                # 윈도우를 새로운 위치로 이동

    # 마우스 클릭 이벤트 처리 메서드
    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()    # 현재 마우스 위치를 저장

    # 마우스 이동 이벤트 처리 메서드
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)        # 이동한 거리 계산
        self.move(self.x() + delta.x(), self.y() + delta.y())   # 윈도우를 이동한 거리만큼 이동
        self.prevPos = event.globalPos()                        # 현재 마우스 위치를 업데이트

# 비밀번호 재설정 class
class resetPwClass(QDialog, resetPw_form_class):
    # 초기화 메서드
    def __init__(self, nickname):
        super().__init__()
        self.setupUi(self)                  # UI 설정 메서드 호출

        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))
        self.nickname = nickname            # 닉네임 초기화

        self.setCenter()                    # 윈도우를 화면 중앙에 배치하는 메서드 호출
        self.prevPos = self.pos()           # 이전 위치 저장 변수 초기화

        self.resetPwBtn: QPushButton        # 비밀번호 재설정 버튼
        self.closeBtn: QPushButton          # 윈도우 종료 버튼
        self.minimizeBtn: QPushButton       # 윈도우 최소화 버튼

        self.iconlabel: QLabel              # 아이콘 레이블
        self.newPwEdit: QLineEdit           # 새로운 비밀번호 입력 필드
        self.newPwValidEdit: QLineEdit      # 새로운 비밀번호 재입력 필드

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))            # 윈도우 끄기 버튼에 아이콘 이미지 삽입
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))      # 윈도우 최소화 버튼에 아이콘 이미지 삽입
        self.iconlabel.setPixmap(                                                   # 아이콘 레이블에 아이콘 이미지 삽입
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.resetPwBtn.clicked.connect(self.resetFunc)     # 비밀번호 재설정 버튼 클릭 시그널과 resetFunc 메서드 연결
        self.closeBtn.clicked.connect(self.gotoMain)        # 윈도우 종료 버튼 클릭 시그널과 gotoMain 메서드 연결
        self.minimizeBtn.clicked.connect(self.minimize)     # 윈도우 최소화 버튼 클릭 시그널과 minimize 메서드 연결

        self.setWindowFlags(Qt.FramelessWindowHint)         # 기본 프레임 없이 설정

    # 최소화 메서드
    def minimize(self):
        self.showMinimized()    # 윈도우 최소화

    # 윈도우 종료 메서드
    def gotoMain(self):
        self.close()            # 윈도우 종료

    # 회원가입 비밀번호 규칙(8자리 이상,하나 이상의 영문,숫자,특수문자로 구성)매칭 메서드
    def checkPWValid(self, edit):
        if re.search('^(?=.*[A-Za-z])(?=.*\d)(?=.*[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"])[A-Za-z\d\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]{8,}$', edit) is None:
            return False
        else:
            return True

    # 비밀번호 재설정 메서드
    def resetFunc(self):                
        pwdValidation = self.checkPWValid(self.newPwEdit.text())                    # 비밀번호 매칭 유효성 확인 

        if not (self.newPwEdit.text() and self.newPwValidEdit.text()):                      # 입력한 값이 없을 경우
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')                            # 메시지 박스 스타일 시트 설정
            QMessageBox.information(
                self, 'PIM agent', "입력하지 않은 정보가 있습니다.", QMessageBox.Yes)
        elif self.newPwEdit.text() != self.newPwValidEdit.text():                           # 새로 입력한 비밀번호가 일치하지 않는 경우
            QMessageBox.information(
                self, 'PIM agent', "새 비밀번호가 일치하지 않습니다.", QMessageBox.Yes)
        elif not pwdValidation:                                                             # 새로 입력한 비밀번호가 규칙에 맞지않는 경우
            QMessageBox.information(
                self, 'PIM agent', "새 비밀번호가 규칙에 맞지 않습니다.", QMessageBox.Yes)
        else:
            resetPw(self.newPwEdit.text(), self.nickname)                                   # 데이터베이스에 비밀번호 업데이트
            QMessageBox.information(
                self, 'PIM agent', "비밀번호가 재설정 되었습니다.", QMessageBox.Yes)
            self.close()                                                                    # 윈도우 종료

    # 윈도우를 화면 중앙에 배치하는 메서드
    def setCenter(self):
        qr = self.frameGeometry()                              # 윈도우의 위치와 크기 정보를 가져옴
        cp = QDesktopWidget().availableGeometry().center()     # 화면의 중심 좌표를 가져옴
        qr.moveCenter(cp)                                      # 윈도우의 중심을 화면의 중심으로 이동
        self.move(qr.topLeft())                                # 윈도우를 새로운 위치로 이동

    # 마우스 클릭 이벤트 처리 메서드
    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()    # 현재 마우스 위치를 저장

    # 마우스 이동 이벤트 처리 메서드
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)        # 이동한 거리 계산
        self.move(self.x() + delta.x(), self.y() + delta.y())   # 윈도우를 이동한 거리만큼 이동
        self.prevPos = event.globalPos()                        # 현재 마우스 위치를 업데이트

# 해상도별로 글자크기를 강제 고정하는 메서드
def adaptation_display():   
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"     # QT 자동 화면 비율 조정 기능 활성화
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"         # QT 화면 비율 조정 요소 설정
    os.environ["QT_SCALE_FACTOR"] = "1"                 # QT 화면 비율 설정

adaptation_display()                                    

stInstance = singleton.SingleInstance()                 # 애플리케이션의 단일 인스턴스를 보장하기 위해 SingleInstance 객체를 생성

app = QApplication(sys.argv)                            # QApplication 객체를 생성
initWindow = initClass(app)                             # initClass 객체를 생성
initWindow.show()                                       # initWindow 윈도우를 화면에 출력
app.exec_()                                             # 애플리케이션의 이벤트 루프를 실행
