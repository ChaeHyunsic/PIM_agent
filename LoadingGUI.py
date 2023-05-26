import keyboard
import pyautogui
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import *

from CustomCrypto import encrypt_all_files
from RunData import guestFileRemove, initLocalCheck, memberFileRemove, memberFileMove

BASE_DIR = os.path.dirname(os.path.abspath(__file__))                                       # 절대경로 사용을 위한 베이스 경로

encryptLoading_form_class = uic.loadUiType(BASE_DIR + r'\UI\encryptLoadingGUI.ui')[0]       # 암호화 진행 상태를 보여주는 ui파일을 불러옴
preGuest_form_class = uic.loadUiType(BASE_DIR + r'\UI\preGuestGui.ui')[0]                   # 파일삭제 진행 상태를 보여주는 ui파일을 불러옴
preMem_form_class = uic.loadUiType(BASE_DIR + r'\UI\preMemGui.ui')[0]                       # 사용자 설정 진행 상태를 보여주는 ui파일을 불러옴

# 포커스를 고정하는 기능을 수행하는 스레드 
class focusOnThread(QThread):
    # 초기화 메서드
    def __init__(self):
        super().__init__()  
        self.breakPoint = False

    # 쓰레드로 동작시킬 함수
    def run(self):
        size = pyautogui.size()                             # 화면 크기를 할당 

        for i in range(150):                            
            keyboard.block_key(i)                           # 키보드의  키(0 - 149)를 blocked 상태로 변경

        while(not self.breakPoint):                     
            try:
                pyautogui.moveTo(size[0]/2, size[1]/2)      # 마우스를 화면 중앙으로 이동
            except:
                pass

# 비 로그인 상태에서 파일을 삭제하는 기능을 수행하는 스레드 
class preGuestThread(QThread):
    preGuest_signal = pyqtSignal()          # 시그널

    # 초기화 메서드
    def __init__(self, srcPath):
        super().__init__()
        self.srcPath = srcPath              # 소스 경로 할당

    # 쓰레드로 동작시킬 함수
    def run(self):
        guestFileRemove(self.srcPath, 0)        # 개인정보 파일과 폴더를 삭제하고, 멀티 프로필 폴더도 제거
        guestFileRemove(self.srcPath, 1)        # 개인정보 파일과 폴더를 삭제하고, 멀티 프로필 폴더도 제거
        self.preGuest_signal.emit()             # 시그널 발생


# 로그인 상태에서 파일을 복호화하고 이동하는 기능을 수행하는 스레드 
class preMemThread(QThread):
    preMem_signal = pyqtSignal()            # 시그널

    # 초기화 메서드
    def __init__(self, nickname, member_setting):
        super().__init__()
        self.nickname = nickname                        # 닉네임 할당
        self.member_setting = member_setting            # 사용자 설정 할당

    # 쓰레드로 동작시킬 함수
    def run(self):
        os.system('taskkill /f /im chrome.exe')         # 크롬 프로세스 종료
        
        while(True):
            try:
                initLocalCheck(self.nickname, self.member_setting)          # 사용자 폴더를 생성하고 복호화, 파일 이동
                break                                                       # 메서드가 정상적으로 수행 시 종료
            except:
                continue                                                    # 예외가 발생하면 다시 수행
        
        self.preMem_signal.emit()                                           # 시그널 발생

# 암호화 기능을 수행하는 스레드 
class encryptThread(QThread):
    encrypt_signal = pyqtSignal()       # 시그널

    # 초기화 메서드
    def __init__(self, srcPath, dstPath, nickname, member_setting):
        super().__init__()
        self.srcPath = srcPath                  # 소스 경로 할당
        self.dstPath = dstPath                  # 목적지 경로 할당
        self.nickname = nickname                # 닉네임 할당
        self.member_setting = member_setting    # 사용자 설정 할당

    # 쓰레드로 동작시킬 함수
    def run(self):
        encrypt_all_files(self.dstPath, self.nickname)                          # 경로 내 모든파일 암호화
        memberFileRemove(self.srcPath, self.nickname, self.member_setting)      # 잔존하는 개인정보 파일과 폴더를 삭제하고 멀티 프로필 폴더 제거
        self.encrypt_signal.emit()                                              # 시그널 발생

# 암호화 진행 상태 화면 class
class EncryptLoadingClass(QDialog, encryptLoading_form_class):
    # 초기화 메서드
    def __init__(self, srcPath, dstPath, nickname, member_setting):
        super().__init__()
        self.setupUi(self)                                                  # UI 설정 메서드 호출
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))      # 윈도우 아이콘을 지정한 아이콘으로 설정
        self.encryptLoadingGIF: QLabel                                      # 로딩윈도우 레이블

        self.srcPath = srcPath                      # 소스 경로 할당
        self.dstPath = dstPath                      # 목적지 경로 할당
        self.nickname = nickname                    # 닉네임 할당
        self.member_setting = member_setting        # 사용자 설정 할당

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |                # 기본 프레임 없이 설정, 화면 가장 위에 표시되도록 설정
                            Qt.FramelessWindowHint)

        self.loadingmovie = QMovie(                                         # QMovie 객체를 생성하고, GIF 파일을 로드
            BASE_DIR + r'\Image\loadingImg.gif', QByteArray(), self)        
        self.loadingmovie.setCacheMode(QMovie.CacheAll)                     # GIF의 모든 프레임을 캐시하여 성능을 향상
        
        self.encryptLoadingGIF.setMovie(self.loadingmovie)                  # QLabel에 동적 이미지 삽입
        self.loadingmovie.start()                                           # GIF 애니메이션 시작

        while(True):            
            try:
                memberFileMove(srcPath, dstPath, nickname, member_setting)      # 사용자 설정 조건에 맞는 파일 이동
                break                                                           # 파일 이동이 성공하면 루프 종료
            except:                                                             # 예외 발생시 다시 수행
                continue

        while(True):            
            try:
                guestFileRemove(srcPath, 0)                                     # 사용자 설정 조건에 해당되지 않는 파일 제거
                guestFileRemove(srcPath, 1)                                     # 사용자 설정 조건에 해당되지 않는 파일 제거
                break                                                           # 파일 제거가 성공하면 루프 종료
            except:                                                             # 예외 발생시 다시 수행
                continue

        self.encryptTh = encryptThread(self.srcPath, self.dstPath, self.nickname, self.member_setting)      # 암호화를 수행하는 스레드 객체 생성
        self.focusOnTh = focusOnThread()                                                                    # 포커스를 고정하는 스레드 객체 생성

        self.encryptTh.encrypt_signal.connect(self.doneLoading)             # encryptTh 객체의 encrypt_signal 시그널을 doneLoading 메서드에 연결

        self.encryptTh.start()                      # 암호화 스레드 실행
        self.focusOnTh.start()                      # 포커스 스레드 실행

    def doneLoading(self):
        self.encryptTh.terminate()                   # 암호화 스레드 종료
        self.focusOnTh.terminate()                   # 포커스 스레드 종료
        keyboard.unhook_all()                        # 키보드 후킹 해제
        self.close()                                 # 윈도우 종료

# 파일 삭제 진행 상태 화면 class
class preGuestClass(QDialog, preGuest_form_class):
    # 초기화 메서드
    def __init__(self, srcPath):
        super().__init__()
        self.setupUi(self)                                                  # UI 설정 메서드 호출
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))      # 윈도우 아이콘을 지정한 아이콘으로 설정
        self.preGuestGIF: QLabel                                            # 로딩윈도우 레이블
        self.srcPath = srcPath                                              # 소스 경로 할당

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |                # 기본 프레임 없이 설정, 화면 가장 위에 표시되도록 설정
                            Qt.FramelessWindowHint)

        self.loadingmovie = QMovie(                                         # QMovie 객체를 생성하고, GIF 파일을 로드
            BASE_DIR + r'\Image\loadingImg.gif', QByteArray(), self)        
        self.loadingmovie.setCacheMode(QMovie.CacheAll)                     # GIF의 모든 프레임을 캐시하여 성능을 향상
        self.preGuestGIF.setMovie(self.loadingmovie)                        # QLabel에 동적 이미지 삽입
        self.loadingmovie.start()                                           # GIF 애니메이션 시작

        self.preGuestTh = preGuestThread(self.srcPath)                      # 파일 삭제 기능을 수행하는 스레드 객체 생성
        self.focusOnTh = focusOnThread()                                    # 포커스를 고정하는 스레드 객체 생성

        self.preGuestTh.preGuest_signal.connect(self.doneProc)              # preGuestTh 객체의 preGuest_signal 시그널을 doneProc 메서드에 연결

        self.preGuestTh.start()                                             # 파일삭제 스레드 실행
        self.focusOnTh.start()                                              # 포커스 스레드 실행

    def doneProc(self):
        self.preGuestTh.terminate()                                         # 파일삭제 스레드 종료
        self.focusOnTh.terminate()                                          # 포커스 스레드 종료
        keyboard.unhook_all()                                               # 키보드 후킹 해제
        self.close()                                                        # 윈도우 종료

# 복호화하고 이동하는 진행 상태 화면 class
class preMemClass(QDialog, preMem_form_class):
    # 초기화 메서드
    def __init__(self, nickname, member_setting):
        super().__init__()
        self.setupUi(self)                                                  # UI 설정 메서드 호출
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))      # 윈도우 아이콘을 지정한 아이콘으로 설정
        self.preMemGIF: QLabel                                              # 로딩윈도우 레이블
        self.nickname = nickname                                            # 소스 경로 할당
        self.member_setting = member_setting                                # 사용자 설정 할당

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |                # 기본 프레임 없이 설정, 화면 가장 위에 표시되도록 설정
                            Qt.FramelessWindowHint)

        self.loadingmovie = QMovie(                                         # QMovie 객체를 생성하고, GIF 파일을 로드
            BASE_DIR + r'\Image\loadingImg.gif', QByteArray(), self)        
        self.loadingmovie.setCacheMode(QMovie.CacheAll)                     # GIF의 모든 프레임을 캐시하여 성능을 향상
        self.preMemGIF.setMovie(self.loadingmovie)                          # QLabel에 동적 이미지 삽입
        self.loadingmovie.start()                                           # GIF 애니메이션 시작

        self.preMemTh = preMemThread(self.nickname, self.member_setting)    # 파일을 복호화하고 이동하는 기능을 수행하는 스레드 객체 생성
        self.focusOnTh = focusOnThread()                                    # 포커스를 고정하는 스레드 객체 생성

        self.preMemTh.preMem_signal.connect(self.doneProc)                  # preGuestTh 객체의 preMem_signal 시그널을 doneProc 메서드에 연결

        self.preMemTh.start()                                               # 복호화, 이동 기능 수행 스레드 실행
        self.focusOnTh.start()                                              # 포커스 스레드 실행

    def doneProc(self):
        self.preMemTh.terminate()                                           # 복호화, 이동 기능 수행 스레드 종료
        self.focusOnTh.terminate()                                          # 포커스 스레드 종료
        keyboard.unhook_all()                                               # 키보드 후킹 해제
        self.close()                                                        # 윈도우 종료
        