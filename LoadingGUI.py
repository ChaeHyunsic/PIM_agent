from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic,QtCore
from PyQt5.QtCore import *

encryptLoading_form_class = uic.loadUiType("encryptLoadingGUI.ui")[0]
decryptLoading_form_class = uic.loadUiType("decryptLoadingGUI.ui")[0]

class encryptLoadingThread(QThread):
    def __init__(self):
        super().__init__()
        self.encryptLoad = EncryptLoadingClass()

    def run(self):
        self.encryptLoad.exec()

    def stop(self):
        self.encryptLoad.doneLoading()
        self.quit()
        self.wait(3000)


class decryptLoadingThread(QThread):
    def __init__(self):
        super().__init__()
        self.decryptLoad = DecryptLoadingClass()

    def run(self):
        self.decryptLoad.exec()

    def stop(self):
        self.decryptLoad.doneLoading()
        self.quit()
        self.wait(3000)


        
class EncryptLoadingClass(QDialog, encryptLoading_form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("windowIcon.png"))

        self.encryptLoadingGIF:QLabel
        
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # 동적 이미지 추가
        self.loadingmovie = QMovie('loadingImg.gif', QByteArray(), self)

        self.loadingmovie.setCacheMode(QMovie.CacheAll)
        # QLabel에 동적 이미지 삽입
        self.encryptLoadingGIF.setMovie(self.loadingmovie)
        self.loadingmovie.start()

    def doneLoading(self):
        self.close()


class DecryptLoadingClass(QDialog, decryptLoading_form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("windowIcon.png"))

        self.decryptLoadingGIF:QLabel

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # 동적 이미지 추가
        self.loadingmovie = QMovie('loadingImg.gif', QByteArray(), self)

        self.loadingmovie.setCacheMode(QMovie.CacheAll)
        # QLabel에 동적 이미지 삽입
        self.decryptLoadingGIF.setMovie(self.loadingmovie)
        self.loadingmovie.start()


    def doneLoading(self):
        self.close()

