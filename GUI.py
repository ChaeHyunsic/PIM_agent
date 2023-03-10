import sys
import re

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *

from Run import runMem, runGuest, trayGuest, trayMem
from RunData import initCheck
from DB_setting import getLoginData, checkIDUnique, checkNicknameUnique, setMembership, getID, getPW, setCustomSetting, getCustomSetting
from LoadingGUI import preMemClass

login_form_class = uic.loadUiType("UI/loginGUI.ui")[0]
run_form_class = uic.loadUiType("UI/runGUI.ui")[0]
join_form_class = uic.loadUiType("UI/joinGUI.ui")[0]
find_form_class = uic.loadUiType("UI/findGUI.ui")[0]

class runGuestThread(QThread):

    # 초기화 메서드 구현
    def __init__(self):
        super().__init__()
        self.breakPoint = False
        self.flag = False

    # 쓰레드로 동작시킬 함수 내용 구현
    def run(self):

        while(not self.breakPoint):
            self.flag = runGuest(self.flag)

    def stop(self):
        self.breakPoint = True
        self.quit()
        self.wait(3000)


class runMemThread(QThread):

    # 초기화 메서드 구현
    def __init__(self, nickname):
        super().__init__()
        self.breakPoint = False
        self.nickname = nickname
        self.flag = False

    # 쓰레드로 동작시킬 함수 내용 구현
    def run(self):

        while(not self.breakPoint):
            self.flag = runMem(self.flag, self.nickname)

    def stop(self):
        self.breakPoint = True
        self.quit()
        self.wait(3000)

class trayGuestThread(QThread):

    def __init__(self, parent=None):
        super().__init__()
        self.breakPoint = False
        self.flag = False

    def run(self):

        while(not self.breakPoint):
            self.flag = trayGuest(self.flag)


class trayMemThread(QThread):

    def __init__(self, nickname, parent=None):
        super().__init__()
        self.breakPoint = False
        self.nickname = nickname
        self.flag = False

    def run(self):

        while(not self.breakPoint):
            self.flag = trayMem(self.flag, self.nickname)

#트레이 아이콘
class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent, seperator, nickname):
        self.icon = icon
        self.seperator = seperator
        self.nickname = nickname
        QSystemTrayIcon.__init__(self, self.icon, parent)
        self.setToolTip("PIM agent")
        
        self.menu = QMenu()
        self.showAction = self.menu.addAction('에이전트 실행')
        self.showAction.triggered.connect(self.showWindow)
        
        self.exitAction = self.menu.addAction('에이전트 종료')
        self.exitAction.triggered.connect(QCoreApplication.instance().quit)
        self.setContextMenu(self.menu)
        
        self.disambiguateTimer = QTimer(self)
        self.disambiguateTimer.setSingleShot(True)
        self.activated.connect(self.onTrayIconActivated)

        if self.seperator == "guest":
            self.th = trayGuestThread()
            self.th.start()
        else:
            self.th = trayMemThread(self.nickname)
            self.th.start()


    def onTrayIconActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.disambiguateTimer.start(qApp.doubleClickInterval())
        elif reason == QSystemTrayIcon.DoubleClick:
            self.disambiguateTimer.stop()
            self.showAction.setDisabled(True)
            self.th.terminate()
            self.hide()
            if self.seperator == "guest":
                preGuest = LoginClass(self)
                preGuest.exec()
            else:
                mainWindow = RunClass(self)
                mainWindow.setNickname(self.nickname)
                mainWindow.setThread()
                mainWindow.exec()

    def showWindow(self):
        self.th.terminate()
        self.hide()
        if self.seperator == "guest":
                preGuest = LoginClass(self)
                preGuest.exec()
        else:
            mainWindow = RunClass(self)
            mainWindow.setNickname(self.nickname)
            mainWindow.setThread()
            mainWindow.exec()


# 로그인 gui


class LoginClass(QDialog, login_form_class):

    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("Image/windowIcon.png"))
        self.app = app

        self.id = ""
        self.password = ""
        self.nickname = ""

        self.idEdit: QLineEdit
        self.pwdEdit: QLineEdit
        self.loginBtn: QPushButton
        self.joinBtn: QPushButton
        self.findBtn: QPushButton
        self.runBackgroundBtn:QPushButton
        self.minimizeBtn:QPushButton

        self.setWindowFlags(Qt.FramelessWindowHint)

        self.runBackgroundBtn.setIcon(QIcon("image/closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon("image/minimizeIcon.png"))

        self.daemonThread = runGuestThread()
        self.daemonThread.start()

        self.loginBtn.clicked.connect(self.btnLoginFunc)
        self.joinBtn.clicked.connect(self.btnJoinFunc)
        self.findBtn.clicked.connect(self.btnFindFunc)
        self.minimizeBtn.clicked.connect(self.minimize)
        self.runBackgroundBtn.clicked.connect(self.runBackground)

        initCheck()

    def minimize(self):
        self.showMinimized()

    def runBackground(self):
        self.daemonThread.terminate()
        self.hide()
        trayicon = TrayIcon(QIcon('Image/windowIcon.png'), self.app, "guest", "guest")
        trayicon.show()

    def btnLoginFunc(self):
        self.id = self.idEdit.text()
        self.password = self.pwdEdit.text()

        if not(self.idEdit.text() and self.pwdEdit.text()):
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')
            QMessageBox.information(
                self, 'Message', "아이디 또는 비밀번호를 입력해 주세요.", QMessageBox.Yes)
            return

        checkLogin, self.nickname = getLoginData(self.id, self.password)
        if(checkLogin):
            self.close()
            self.daemonThread.stop()
            
            preMemThread = preMemClass(self.nickname)
            preMemThread.exec()

            mainWindow = RunClass(self.app)
            mainWindow.setNickname(self.nickname)
            mainWindow.setThread()

            mainWindow.exec()
        else:
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')
            QMessageBox.information(
                self, 'Message', "입력하신 회원 정보와 일치하는 계정이 없습니다.", QMessageBox.Yes)
            return

    def btnJoinFunc(self):
        self.hide()
        joinWindow = JoinClass(self)
        joinWindow.exec()
        self.show()

    def btnFindFunc(self):
        self.hide()
        findWindow = FindClass(self)
        findWindow.exec()
        self.show()


class RunClass(QDialog, run_form_class):

    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.trayIcon = QSystemTrayIcon(QIcon("Image/windowIcon.png"), parent = self.app)

        self.nickname = ""
        self.titleLabel: QLabel
        
        self.bookmarkCheckBox:QCheckBox
        self.visitCheckBox:QCheckBox
        self.downloadCheckBox:QCheckBox
        self.autoFormCheckBox:QCheckBox
        self.cookieCheckBox:QCheckBox
        self.cacheCheckBox:QCheckBox
        self.sessionCheckBox:QCheckBox
        self.setDBBtn:QPushButton
        self.logoutBtn: QPushButton
        self.runBackgroundBtn:QPushButton
        self.minimizeBtn:QPushButton
        
        self.runBackgroundBtn.setIcon(QIcon("Image/closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon("Image/minimizeIcon.png"))

        self.setWindowIcon(QIcon("Image/windowIcon.png"))

        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.setWindowFlags(Qt.FramelessWindowHint)

        self.setDBBtn.clicked.connect(self.setDB)
        self.logoutBtn.clicked.connect(self.logout)
        self.minimizeBtn.clicked.connect(self.minimize)
        self.runBackgroundBtn.clicked.connect(self.runBackground)
    
    def setNickname(self, nickname):
        self.nickname = nickname
        self.titleLabel.setText(nickname + " 님")

        checkRetval = getCustomSetting(self.nickname)

        if checkRetval[0] == 0:
            self.bookmarkCheckBox.toggle()
        if checkRetval[1] == 0:
            self.visitCheckBox.toggle()
        if checkRetval[2] == 0:
            self.downloadCheckBox.toggle()
        if checkRetval[3] == 0:
            self.autoFormCheckBox.toggle()
        if checkRetval[4] == 0:
            self.cookieCheckBox.toggle()
        if checkRetval[5] == 0:
            self.cacheCheckBox.toggle()
        if checkRetval[6] == 0:
            self.sessionCheckBox.toggle()

    def setThread(self):
        # start 메소드 호출 -> 자동으로 run 메소드 호출
        self.daemonThread = runMemThread(self.nickname)
        self.daemonThread.start()

    def setDB(self):
        bookmarkCheck = 1 if self.bookmarkCheckBox.isChecked() is True else 0
        visitCheck = 1 if self.visitCheckBox.isChecked() is True else 0
        downloadCheck = 1 if self.downloadCheckBox.isChecked() is True else 0
        autoFormCheck = 1 if self.autoFormCheckBox.isChecked() is True else 0
        cookieCheck = 1 if self.cookieCheckBox.isChecked() is True else 0
        cacheCheck = 1 if self.cacheCheckBox.isChecked() is True else 0
        sessionCheck = 1 if self.sessionCheckBox.isChecked() is True else 0

        setCustomSetting(bookmarkCheck, visitCheck, downloadCheck, autoFormCheck, cookieCheck, cacheCheck, sessionCheck, self.nickname)

    def minimize(self):
        self.showMinimized()

    def runBackground(self):
        self.hide()
        self.daemonThread.terminate()
        trayicon = TrayIcon(QIcon('Image/windowIcon.png'), self.app, "member", self.nickname)
        trayicon.show()

        self.trayIcon.hide()

    def logout(self):
        self.daemonThread.stop()
        self.close()
        preGuest = LoginClass(self.app)
        preGuest.exec()


# 회원가입 gui
class JoinClass(QDialog, join_form_class):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.idEdit: QLineEdit
        self.pwdEdit: QLineEdit
        self.pwdCheckEdit: QLineEdit
        self.nicknameEdit: QLineEdit
        self.joinBtn: QPushButton
        self.gotoMainBtn: QPushButton

        self.idEdit.setText("")
        self.pwdEdit.setText("")
        self.pwdCheckEdit.setText("")
        self.nicknameEdit.setText("")

        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.joinBtn.clicked.connect(self.join)
        self.gotoMainBtn.clicked.connect(self.gotoMain)

    def checkIDPWValid(self, edit):
        if re.search('^(?!.*\s)(?!.*[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"])(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,16}$', edit) is None:
            return False
        else:
            return True

    def nicknameValid(self, nickname):
        if re.search('^(?!.*\s)(?=.*[a-zA-Z0-9ㄱ-ㅎ가-힣]).{0,16}$', nickname) is None:
            return False
        else:
            return True

    def join(self):
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        idValidation = self.checkIDPWValid(self.idEdit.text())
        pwdValidation = self.checkIDPWValid(self.pwdEdit.text())
        nicknameValidation = self.nicknameValid(self.nicknameEdit.text())

        if not(self.idEdit.text() and self.pwdEdit.text() and self.pwdCheckEdit.text() and self.nicknameEdit.text()):
            QMessageBox.information(
                self, 'Message', "입력하지 않은 정보가 있습니다.", QMessageBox.Yes)
        elif not idValidation:
            QMessageBox.information(
                self, 'Message', "입력한 ID가 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not pwdValidation:
            QMessageBox.information(
                self, 'Message', "입력한 PW가 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif self.pwdEdit.text() != self.pwdCheckEdit.text():
            QMessageBox.information(
                self, 'Message', "입력한 PW와 재확인한 PW가 일치하지 않습니다.", QMessageBox.Yes)
        elif not nicknameValidation:
            QMessageBox.information(
                self, 'Message', "입력한 닉네임이 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not checkIDUnique(self.idEdit.text()):
            QMessageBox.information(
                self, 'Message', "입력한 ID가 이미 존재합니다.", QMessageBox.Yes)
        elif not checkNicknameUnique(self.nicknameEdit.text()):
            QMessageBox.information(
                self, 'Message', "입력한 닉네임이 이미 존재합니다.", QMessageBox.Yes)
        else:
            setMembership(self.idEdit.text(), self.pwdEdit.text(), self.nicknameEdit.text())

            self.close()

    def gotoMain(self):
        self.close()


# 회원정보 찾기 gui
class FindClass(QDialog, find_form_class):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.findIdFromNicknameEdit: QLineEdit
        self.findPwFromIDEdit: QLineEdit
        self.findPwFromNicknameEdit: QLineEdit

        self.findIDBtn: QPushButton
        self.findPWBtn: QPushButton
        self.gotoMainBtn: QPushButton

        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.findIDBtn.clicked.connect(self.findIDFunc)
        self.findPWBtn.clicked.connect(self.findPWFunc)
        self.gotoMainBtn.clicked.connect(self.gotoMain)

    def findIDFunc(self):
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        if not self.findIdFromNicknameEdit.text():
            QMessageBox.information(
                self, 'Message', "닉네임이 입력되지 않았습니다.", QMessageBox.Yes)
        else:
            result, resultID = getID(self.findIdFromNicknameEdit.text())

            if(result):
                QMessageBox.information(
                self, 'Message', "해당 닉네임으로 연결된 ID는 " + resultID + " 입니다.", QMessageBox.Yes)
            else:
                QMessageBox.information(
                self, 'Message', "해당 닉네임으로 연결된 ID는 없습니다.", QMessageBox.Yes)
            
            self.close()

    def findPWFunc(self):
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        if not(self.findPwFromIDEdit.text() and self.findPwFromNicknameEdit.text()):
            QMessageBox.information(
                self, 'Message', "ID나 닉네임이 입력되지 않았습니다.", QMessageBox.Yes)
        else:
            result, resultPW = getPW(self.findPwFromIDEdit.text(), self.findPwFromNicknameEdit.text())

            if(result):
                QMessageBox.information(
                self, 'Message', "해당 ID와 닉네임으로 연결된 PW는 " + resultPW + " 입니다.", QMessageBox.Yes)
            else:
                QMessageBox.information(
                self, 'Message', "해당 ID와 닉네임으로 연결된 PW는 없습니다.", QMessageBox.Yes)
            self.close()

    def gotoMain(self):
        self.close()


app = QApplication(sys.argv)
loginWindow = LoginClass(app)
loginWindow.show()
app.exec_()
