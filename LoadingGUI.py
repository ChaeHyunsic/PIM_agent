import keyboard, pyautogui
import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import *

from CustomCrypto import encrypt_all_files, decrypt_all_files


encryptLoading_form_class = uic.loadUiType("encryptLoadingGUI.ui")[0]
decryptLoading_form_class = uic.loadUiType("decryptLoadingGUI.ui")[0]

class focusOnThread(QThread):
    
    def __init__(self):
        super().__init__()
        self.breakPoint = False
        
    def run(self):
        size = pyautogui.size()
        while(not self.breakPoint):
            try:
                pyautogui.moveTo(size[0]/2, size[1]/2) 
                if keyboard.is_pressed('win'):
                    time.sleep(0.3)
                    pyautogui.press('winleft')
                if keyboard.is_pressed('alt'):
                    time.sleep(0.3)
                    pyautogui.press('esc')

            except:
                pass

    def stop(self):
        self.breakPoint = True
        self.terminate()
        self.wait(3000)

class encryptThread(QThread):
    encrypt_signal = pyqtSignal(bool)

    def __init__(self, dstPath, nickname):
        super().__init__()
        self.dstPath = dstPath
        self.nickname = nickname
        self.retval = False
    
    def run(self):
        self.retval = encrypt_all_files(self.dstPath, self.nickname)
        self.encrypt_signal.emit(self.retval)


class decryptThread(QThread):
    decrypt_signal = pyqtSignal(bool)

    def __init__(self, dstPath, nickname):
        super().__init__()
        self.dstPath = dstPath
        self.nickname = nickname
        self.retval = False
    
    def run(self):
        self.retval = decrypt_all_files(self.dstPath, self.nickname)
        self.decrypt_signal.emit(self.retval)


class EncryptLoadingClass(QDialog, encryptLoading_form_class):

    def __init__(self, dstPath, nickname):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("windowIcon.png"))
        self.encryptLoadingGIF:QLabel

        self.dstPath = dstPath
        self.nickname = nickname
        
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # 동적 이미지 추가
        self.loadingmovie = QMovie('loadingImg.gif', QByteArray(), self)
        self.loadingmovie.setCacheMode(QMovie.CacheAll)

        # QLabel에 동적 이미지 삽입
        self.encryptLoadingGIF.setMovie(self.loadingmovie)
        self.loadingmovie.start()

        self.encryptTh = encryptThread(self.dstPath, self.nickname)
        self.focusOnTh = focusOnThread()

        self.encryptTh.encrypt_signal.connect(self.doneLoading)

        self.encryptTh.start()
        self.focusOnTh.start()


    def doneLoading(self,retval):
        if retval == True:
            self.focusOnTh.terminate()
            self.close()


class DecryptLoadingClass(QDialog, decryptLoading_form_class):
    def __init__(self, dstPath, nickname):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("windowIcon.png"))
        
        self.decryptLoadingGIF:QLabel

        self.dstPath = dstPath
        self.nickname = nickname

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # 동적 이미지 추가
        self.loadingmovie = QMovie('loadingImg.gif', QByteArray(), self)
        self.loadingmovie.setCacheMode(QMovie.CacheAll)

        # QLabel에 동적 이미지 삽입
        self.decryptLoadingGIF.setMovie(self.loadingmovie)
        self.loadingmovie.start()

        self.decryptTh = decryptThread(self.dstPath, self.nickname)
        self.focusOnTh = focusOnThread()

        self.decryptTh.decrypt_signal.connect(self.doneLoading)

        self.decryptTh.start()
        self.focusOnTh.start()

    def doneLoading(self,retval):
        if retval == True:
            self.focusOnTh.terminate()
            self.close()