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
from RunData import initCheck, getSrcPath, getDstPath, memberFileMove
from DB_setting import getLoginData, checkIDUnique, checkNicknameUnique, setMembership, getID, getEmail, resetPw, setCustomSetting, getCustomSetting
from LoadingGUI import preGuestClass, preMemClass, EncryptLoadingClass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

init_form_class = uic.loadUiType(BASE_DIR + r'\UI\initGUI.ui')[0]
login_form_class = uic.loadUiType(BASE_DIR + r'\UI\loginGUI.ui')[0]
run_form_class = uic.loadUiType(BASE_DIR + r'\UI\runGUI.ui')[0]
join_form_class = uic.loadUiType(BASE_DIR + r'\UI\joinGUI.ui')[0]
find_form_class = uic.loadUiType(BASE_DIR + r'\UI\findGUI.ui')[0]
validEmail_form_class = uic.loadUiType(BASE_DIR + r'\UI\validEmailGui.ui')[0]
resetPw_form_class = uic.loadUiType(BASE_DIR + r'\UI\resetPwGui.ui')[0]

class runGuestThread(QThread):
    timeout_signal = pyqtSignal()

    # 초기화 메서드 구현
    def __init__(self):
        super().__init__()
        self.breakPoint = False
        self.flag = False
        self.acc = 0
        self.var = 0

    # 쓰레드로 동작시킬 함수 내용 구현
    def run(self):
        while(not self.breakPoint):
            self.var, self.acc, self.flag = runGuest(self.var, self.acc)
            if self.flag == True:
                self.breakPoint = True
                self.quit()
                self.timeout_signal.emit()


class runMemThread(QThread):
    encrypt_signal = pyqtSignal(bool)

    # 초기화 메서드 구현
    def __init__(self):
        super().__init__()
        self.breakPoint = False
        self.flag = False

    # 쓰레드로 동작시킬 함수 내용 구현
    def run(self):
        while(not self.breakPoint):
            self.flag = runMem(self.flag)
            if self.flag == True:
                self.breakPoint = True
                self.quit()
                self.encrypt_signal.emit(self.flag)


class trayGuestThread(QThread):

    def __init__(self, parent=None):
        super().__init__()
        self.breakPoint = False
        self.flag = False

    def run(self):

        while(not self.breakPoint):
            self.flag = trayGuest(self.flag)


class trayMemThread(QThread):
    encrypt_signal = pyqtSignal(bool)

    def __init__(self, nickname, member_setting, parent=None):
        super().__init__()
        self.breakPoint = False
        self.nickname = nickname
        self.member_setting = member_setting
        self.flag = False

    def run(self):
        while(not self.breakPoint):
            self.flag = trayMem(self.flag, self.nickname, self.member_setting)
            if self.flag == True:
                self.breakPoint = True
                self.encrypt_signal.emit(self.flag)

# 트레이 아이콘
class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent, seperator, nickname, member_setting):
        self.icon = icon
        self.seperator = seperator
        self.nickname = nickname
        self.member_setting = member_setting
        QSystemTrayIcon.__init__(self, self.icon, parent)
        self.setToolTip("PIM agent")

        self.menu = QMenu()
        self.showAction = self.menu.addAction('에이전트 실행')
        self.showAction.triggered.connect(self.showWindow)

        self.logoutAction = self.menu.addAction("유저 로그아웃")
        self.logoutAction.triggered.connect(self.logout)

        self.exitAction = self.menu.addAction('에이전트 종료')
        self.exitAction.triggered.connect(self.exit)

        self.setContextMenu(self.menu)

        self.logoutAction.setEnabled(False)

        self.disambiguateTimer = QTimer(self)
        self.disambiguateTimer.setSingleShot(True)
        self.activated.connect(self.onTrayIconActivated)

        if self.seperator == "guest":
            self.th = trayGuestThread()
            self.th.start()
        else:
            self.logoutAction.setEnabled(True)
            self.th = trayMemThread(self.nickname, self.member_setting)
            self.th.start()
            self.th.encrypt_signal.connect(self.autoLogout)

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
                mainWindow.setValue(self.nickname, self.member_setting)
                mainWindow.setThread()
                mainWindow.exec()

    def showWindow(self):
        self.hide()
        if self.seperator == "guest":
            preGuest = LoginClass(self)
            preGuest.exec()
        else:
            mainWindow = RunClass(self)
            mainWindow.setValue(self.nickname, self.member_setting)
            mainWindow.setThread()
            mainWindow.exec()

    def setSeperator(self, seperator):
        self.seperator = seperator

    def logout(self):
        os.system('taskkill /f /im chrome.exe')
        time.sleep(1)

        self.th.terminate()
        self.setSeperator("guest")
        self.logoutAction.setEnabled(False)

        memberFileMove(getSrcPath(), getDstPath(self.nickname), self.nickname, self.member_setting) # 파일 옮기기
        encryptInTrayIcon(getSrcPath(), getDstPath(self.nickname), self.nickname, self.member_setting)

        self.th = trayGuestThread()
        self.th.start()

    def autoLogout(self):
        self.th.terminate()
        self.setSeperator("guest")
        self.logoutAction.setEnabled(False)

        self.th = trayGuestThread()
        self.th.start()

    def exit(self):
        if self.seperator == "guest":
            self.setVisible(False)
            QCoreApplication.instance().quit()
        else:
            self.setVisible(False)
            os.system('taskkill /f /im chrome.exe')
            time.sleep(1)

            self.th.terminate()
            memberFileMove(getSrcPath(), getDstPath(self.nickname), self.nickname, self.member_setting) # 파일 옮기기
            encryptInTrayIcon(getSrcPath(), getDstPath(self.nickname), self.nickname, self.member_setting)
            QCoreApplication.instance().quit()


class initClass(QDialog, init_form_class):
    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.logolabel: QLabel
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))
        self.setCenter()
        self.prevPos = self.pos()

        self.logolabel.setPixmap(QPixmap(BASE_DIR + r"\Image\initLogo.png"))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        QTimer.singleShot(2500, self.endTitle)

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def endTitle(self):
        self.close()

        preGuest = LoginClass(app)
        preGuest.exec()

# 로그인 gui
class LoginClass(QDialog, login_form_class):

    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))
        self.app = app

        self.srcPath = getSrcPath()
        self.setCenter()
        self.prevPos = self.pos()

        self.id = ""
        self.password = ""
        self.nickname = ""

        self.idEdit: QLineEdit
        self.pwdEdit: QLineEdit
        self.loginBtn: QPushButton
        self.joinBtn: QPushButton
        self.findBtn: QPushButton
        self.runBackgroundBtn: QPushButton
        self.minimizeBtn: QPushButton
        self.iconlabel: QLabel

        self.setWindowFlags(Qt.FramelessWindowHint)

        self.runBackgroundBtn.setIcon(
            QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))
        self.iconlabel.setPixmap(
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.daemonThread = runGuestThread()
        self.daemonThread.timeout_signal.connect(self.loading)
        self.daemonThread.start()

        self.loginBtn.clicked.connect(self.btnLoginFunc)
        self.joinBtn.clicked.connect(self.btnJoinFunc)
        self.findBtn.clicked.connect(self.btnFindFunc)
        self.minimizeBtn.clicked.connect(self.minimize)
        self.runBackgroundBtn.clicked.connect(self.runBackground)

        initCheck()

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.prevPos = event.globalPos()

    def loading(self):
        self.close()

        preGuestclass = preGuestClass(self.srcPath)
        preGuestclass.exec()

        preGuest = LoginClass(self.app)
        preGuest.exec()

    def minimize(self):
        self.showMinimized()

    def runBackground(self):
        self.daemonThread.terminate()
        self.hide()
        trayicon = TrayIcon(QIcon(BASE_DIR + r'\Image\windowIcon.png'), self.app, "guest", "guest", None)
        trayicon.setVisible(True)
        trayicon.show()

    def btnLoginFunc(self):
        self.id = self.idEdit.text()
        self.password = self.pwdEdit.text()

        if not(self.idEdit.text() and self.pwdEdit.text()):
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')
            QMessageBox.information(
                self, 'PIM agent', "아이디 또는 비밀번호를 입력해 주세요.", QMessageBox.Yes)
            return

        try:
            checkLogin, self.nickname = getLoginData(self.id, self.password)
            member_setting = getCustomSetting(self.nickname)

            if(checkLogin):
                self.close()
                self.daemonThread.terminate()

                preMemThread = preMemClass(self.nickname, member_setting)
                preMemThread.exec()

                mainWindow = RunClass(self.app)
                mainWindow.setValue(self.nickname, member_setting)
                mainWindow.setThread()

                mainWindow.exec()
        except Exception as e:
            # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            if str(e) ==  '(2003, \"Can\'t connect to MySQL server on \'3.39.9.144\' (timed out)\")':
                QMessageBox.setStyleSheet(
                        self, 'QMessageBox {color: rgb(120, 120, 120)}')
                QMessageBox.information(
                    self, 'PIM agent', "원격 네트워크 환경을 확인해주세요.", QMessageBox.Yes)
            elif str(e) == 'tuple index out of range':
                QMessageBox.setStyleSheet(
                    self, 'QMessageBox {color: rgb(120, 120, 120)}')
                QMessageBox.information(
                    self, 'PIM agent', "입력하신 회원 정보와 일치하는 계정이 없습니다.", QMessageBox.Yes)
            else:
                QMessageBox.setStyleSheet(
                        self, 'QMessageBox {color: rgb(120, 120, 120)}')
                QMessageBox.information(
                    self, 'PIM agent', "로컬 네트워크 환경을 확인해주세요.", QMessageBox.Yes)

    def btnJoinFunc(self):
        self.setCenter()
        self.daemonThread.terminate()
        self.close()
        joinWindow = JoinClass(app)
        joinWindow.exec()

    def btnFindFunc(self):
        self.setCenter()
        self.daemonThread.terminate()
        self.close()
        findWindow = FindClass(app)
        findWindow.exec()


class RunClass(QDialog, run_form_class):

    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.app = app

        self.setCenter()
        self.prevPos = self.pos()

        self.nickname = ""
        self.member_setting = None

        self.titleLabel: QLabel
        self.iconlabel: QLabel

        self.bookmarkCheckBox: QCheckBox
        self.visitCheckBox: QCheckBox
        self.downloadCheckBox: QCheckBox
        self.autoFormCheckBox: QCheckBox
        self.cookieCheckBox: QCheckBox
        self.cacheCheckBox: QCheckBox
        self.sessionCheckBox: QCheckBox
        self.setDBBtn: QPushButton
        self.logoutBtn: QPushButton
        self.runBackgroundBtn: QPushButton
        self.minimizeBtn: QPushButton

        self.iconlabel.setPixmap(
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))
        self.runBackgroundBtn.setIcon(
            QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))

        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))

        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.setWindowFlags(Qt.FramelessWindowHint)

        self.setDBBtn.clicked.connect(self.setDB)
        self.logoutBtn.clicked.connect(self.logout)
        self.minimizeBtn.clicked.connect(self.minimize)
        self.runBackgroundBtn.clicked.connect(self.runBackground)

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.prevPos = event.globalPos()

    def setValue(self, nickname, member_setting):
        self.nickname = nickname
        self.member_setting = member_setting
        
        self.titleLabel.setText(nickname + " 님")

        if member_setting[0] == 0:
            self.bookmarkCheckBox.toggle()
        if member_setting[1] == 0:
            self.visitCheckBox.toggle()
        if member_setting[2] == 0:
            self.downloadCheckBox.toggle()
        if member_setting[3] == 0:
            self.autoFormCheckBox.toggle()
        if member_setting[4] == 0:
            self.cookieCheckBox.toggle()
        if member_setting[5] == 0:
            self.cacheCheckBox.toggle()
        if member_setting[6] == 0:
            self.sessionCheckBox.toggle()

    def setThread(self):
        # start 메소드 호출 -> 자동으로 run 메소드 호출
        self.daemonThread = runMemThread()
        self.daemonThread.start()
        self.daemonThread.encrypt_signal.connect(self.logout)

    def setDB(self):
        bookmarkCheck = 1 if self.bookmarkCheckBox.isChecked() is True else 0
        visitCheck = 1 if self.visitCheckBox.isChecked() is True else 0
        downloadCheck = 1 if self.downloadCheckBox.isChecked() is True else 0
        autoFormCheck = 1 if self.autoFormCheckBox.isChecked() is True else 0
        cookieCheck = 1 if self.cookieCheckBox.isChecked() is True else 0
        cacheCheck = 1 if self.cacheCheckBox.isChecked() is True else 0
        sessionCheck = 1 if self.sessionCheckBox.isChecked() is True else 0

        try:
            setCustomSetting(bookmarkCheck, visitCheck, downloadCheck, autoFormCheck, cookieCheck, cacheCheck, sessionCheck, self.nickname)
        except pymysql.err.OperationalError:
            QMessageBox.information(self, 'PIM agent', "요청이 너무 많아 응답이 지연되고 있습니다.\n잠시 후 다시 시도바랍니다.", QMessageBox.Yes)
            pass

        self.member_setting = (bookmarkCheck, visitCheck, downloadCheck, autoFormCheck, cookieCheck, cacheCheck, sessionCheck)

        self.daemonThread.terminate() 
        self.daemonThread = runMemThread()
        self.daemonThread.start()
        self.daemonThread.encrypt_signal.connect(self.logout)

        QMessageBox.setStyleSheet(self, 'QMessageBox {color: rgb(120, 120, 120)}')
        QMessageBox.information(self, 'PIM agent', "사용자 설정이 완료되었습니다.", QMessageBox.Yes)

    def minimize(self):
        self.showMinimized()

    def runBackground(self):
        self.hide()
        self.daemonThread.terminate()
        trayicon = TrayIcon(
            QIcon(BASE_DIR + r'\Image\windowIcon.png'), self.app, "member", self.nickname, self.member_setting)
        trayicon.show()

    def logout(self):
        self.daemonThread.terminate()
        self.close()

        os.system('taskkill /f /im chrome.exe')
        time.sleep(1)

        memberFileMove(getSrcPath(), getDstPath(self.nickname), self.nickname, self.member_setting)   
            
        encryptThread = EncryptLoadingClass(getSrcPath(), getDstPath(self.nickname), self.nickname, self.member_setting)
        encryptThread.exec()

        preGuest = LoginClass(self.app)
        preGuest.exec()


# 회원가입 gui
class JoinClass(QDialog, join_form_class):
    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.app = app

        self.setCenter()
        self.prevPos = self.pos()

        self.idEdit: QLineEdit
        self.pwdEdit: QLineEdit
        self.emailEdit: QLineEdit
        self.nicknameEdit: QLineEdit
        self.joinBtn: QPushButton
        self.gotoMainBtn: QPushButton
        self.iconlabel: QLabel
        self.closeBtn: QPushButton
        self.minimizeBtn: QPushButton

        self.idEdit.setText("")
        self.pwdEdit.setText("")
        self.emailEdit.setText("")
        self.nicknameEdit.setText("")

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))
        self.iconlabel.setPixmap(
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.joinBtn.clicked.connect(self.join)
        self.closeBtn.clicked.connect(self.gotoMain)
        self.gotoMainBtn.clicked.connect(self.gotoMain)
        self.minimizeBtn.clicked.connect(self.minimize)

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.prevPos = event.globalPos()

    def checkIDValid(self, edit):
        if re.search('^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,12}$', edit) is None:
            return False
        else:
            return True

    def checkPWValid(self, edit):
        if re.search('^(?=.*[A-Za-z])(?=.*\d)(?=.*[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"])[A-Za-z\d\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]{8,}$', edit) is None:
            return False
        else:
            return True

    def emailValid(self, edit):
        if re.search('^[a-zA-Z0-9._-]+@[a-zA-Z0-9.]+\.[a-zA-Z]{2,4}$', edit) is None:
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
        idValidation = self.checkIDValid(self.idEdit.text())
        pwdValidation = self.checkPWValid(self.pwdEdit.text())
        emailValidation = self.emailValid(self.emailEdit.text())
        nicknameValidation = self.nicknameValid(self.nicknameEdit.text())

        if not(self.idEdit.text() and self.pwdEdit.text() and self.emailEdit.text() and self.nicknameEdit.text()):
            QMessageBox.information(
                self, 'PIM agent', "입력하지 않은 정보가 있습니다.", QMessageBox.Yes)
        elif not idValidation:
            QMessageBox.information(
                self, 'PIM agent', "입력한 ID가 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not pwdValidation:
            QMessageBox.information(
                self, 'PIM agent', "입력한 PW가 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not emailValidation:
            QMessageBox.information(
                self, 'PIM agent', "이메일 형식이 잘못되었습니다.", QMessageBox.Yes)
        elif not nicknameValidation:
            QMessageBox.information(
                self, 'PIM agent', "입력한 닉네임이 회원가입 규칙에 맞지않습니다.", QMessageBox.Yes)
        elif not checkIDUnique(self.idEdit.text()):
            QMessageBox.information(
                self, 'PIM agent', "입력한 ID가 이미 존재합니다.", QMessageBox.Yes)
        elif not checkNicknameUnique(self.nicknameEdit.text()):
            QMessageBox.information(
                self, 'PIM agent', "입력한 닉네임이 이미 존재합니다.", QMessageBox.Yes)
        else:
            setMembership(self.idEdit.text(), self.pwdEdit.text(), self.emailEdit.text(), self.nicknameEdit.text())
            QMessageBox.information(self, 'PIM agent', "회원가입에 성공하였습니다.", QMessageBox.Yes)
            self.close()

            preGuest = LoginClass(self.app)
            preGuest.exec()

    def minimize(self):
        self.showMinimized()

    def gotoMain(self):
        self.close()
        preGuest = LoginClass(self.app)
        preGuest.exec()


# 회원정보 찾기 gui
class FindClass(QDialog, find_form_class):
    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.app = app

        self.setCenter()
        self.prevPos = self.pos()

        self.findIdFromNicknameEdit: QLineEdit
        self.findPwFromIDEdit: QLineEdit
        self.findPwFromNicknameEdit: QLineEdit

        self.findIDBtn: QPushButton
        self.findPWBtn: QPushButton
        self.gotoMainBtn: QPushButton
        self.iconlabel: QLabel
        self.closeBtn: QPushButton
        self.minimizeBtn: QPushButton

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))
        self.iconlabel.setPixmap(
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.findIDBtn.clicked.connect(self.findIDFunc)
        self.findPWBtn.clicked.connect(self.resetPWFunc)
        self.closeBtn.clicked.connect(self.gotoMain)
        self.minimizeBtn.clicked.connect(self.minimize)
        self.gotoMainBtn.clicked.connect(self.gotoMain)

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.prevPos = event.globalPos()

    def findIDFunc(self):
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        if not self.findIdFromNicknameEdit.text():
            QMessageBox.information(
                self, 'PIM agent', "닉네임이 입력되지 않았습니다.", QMessageBox.Yes)
        else:
            result, resultID = getID(self.findIdFromNicknameEdit.text())

            if(result):
                QMessageBox.information(self, 'PIM agent', "해당 닉네임으로 연결된 ID는 " + resultID[:-3] + "***" + " 입니다.", QMessageBox.Yes)
                self.close()

                preGuest = LoginClass(self.app)
                preGuest.exec()  
            else:
                QMessageBox.information(self, 'PIM agent', "해당 닉네임으로 연결된 ID는 없습니다.", QMessageBox.Yes)


    def resetPWFunc(self):
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        if not(self.findPwFromIDEdit.text() and self.findPwFromNicknameEdit.text()):
            QMessageBox.information(self, 'PIM agent', "ID나 닉네임이 입력되지 않았습니다.", QMessageBox.Yes)
        else:
            result, resultEmail = getEmail(self.findPwFromIDEdit.text(), self.findPwFromNicknameEdit.text())

            if(result):
                self.close()
                validCodeClass = ValidCodeClass(resultEmail, self.findPwFromNicknameEdit.text(), self.app)
                validCodeClass.exec()
            else:
                QMessageBox.information(self, 'PIM agent', "해당 ID와 닉네임으로 연결된 PW는 없습니다.", QMessageBox.Yes)
            self.close()

    def minimize(self):
        self.showMinimized()

    def gotoMain(self):
        self.close()

        preGuest = LoginClass(self.app)
        preGuest.exec()


class ValidCodeClass(QDialog, validEmail_form_class):
    def __init__(self, email, nickname, app):
        super().__init__()
        self.setupUi(self)
        self.app = app

        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))
        self.email = email
        self.send_time = time.time()
        self.code = sendMail(self.email)
        self.nickname = nickname

        self.setCenter()
        self.prevPos = self.pos()

        self.validBtn: QPushButton
        self.resendBtn: QPushButton
        self.closeBtn: QPushButton
        self.minimizeBtn: QPushButton

        self.iconlabel: QLabel

        self.codeEdit: QLineEdit

        self.codeEdit.setText("")

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))
        self.iconlabel.setPixmap(
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.validBtn.clicked.connect(self.validFunc)
        self.resendBtn.clicked.connect(self.resendFunc)
        self.closeBtn.clicked.connect(self.gotoMain)
        self.minimizeBtn.clicked.connect(self.minimize)

        self.setWindowFlags(Qt.FramelessWindowHint)

    def minimize(self):
        self.showMinimized()

    def gotoMain(self):
        self.close()

        preGuest = LoginClass(self.app)
        preGuest.exec()

    def validFunc(self):
        if not self.codeEdit.text():
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')
            QMessageBox.information(
                self, 'PIM agent', "인증코드가 입력되지 않았습니다.", QMessageBox.Yes)
        elif time.time() - self.send_time > 600:
            QMessageBox.information(
                self, 'PIM agent', "인증코드가 만료되었습니다. 재시도 바랍니다.", QMessageBox.Yes)
        elif self.codeEdit.text() == self.code:
            self.close()
            resetPw = resetPwClass(self.nickname, self.app)
            resetPw.exec()
        else:
            QMessageBox.information(
                self, 'PIM agent', "인증코드가 일치하지 않습니다.", QMessageBox.Yes)

    def resendFunc(self):
        self.send_time = time.time()
        self.code = sendMail(self.email)
        QMessageBox.setStyleSheet(
            self, 'QMessageBox {color: rgb(120, 120, 120)}')
        QMessageBox.information(
            self, 'PIM agent', "인증코드를 재전송 하였습니다.", QMessageBox.Yes)

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.prevPos = event.globalPos()


class resetPwClass(QDialog, resetPw_form_class):
    def __init__(self, nickname, app):
        super().__init__()
        self.setupUi(self)
        self.app = app

        self.setWindowIcon(QIcon(BASE_DIR + r"\Image\windowIcon.png"))
        self.nickname = nickname

        self.setCenter()
        self.prevPos = self.pos()

        self.resetPwBtn: QPushButton
        self.closeBtn: QPushButton
        self.minimizeBtn: QPushButton

        self.iconlabel: QLabel

        self.newPwEdit: QLineEdit
        self.newPwValidEdit: QLineEdit

        self.closeBtn.setIcon(QIcon(BASE_DIR + r"\Image\closeIcon.png"))
        self.minimizeBtn.setIcon(QIcon(BASE_DIR + r"\Image\minimizeIcon.png"))
        self.iconlabel.setPixmap(
            QPixmap(BASE_DIR + r"\Image\windowIcon.png").scaled(QSize(21, 20)))

        self.resetPwBtn.clicked.connect(self.resetFunc)
        self.closeBtn.clicked.connect(self.gotoMain)
        self.minimizeBtn.clicked.connect(self.minimize)

        self.setWindowFlags(Qt.FramelessWindowHint)

    def minimize(self):
        self.showMinimized()

    def gotoMain(self):
        self.close()

        preGuest = LoginClass(self.app)
        preGuest.exec()

    def checkPWValid(self, edit):
        if re.search('^(?=.*[A-Za-z])(?=.*\d)(?=.*[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"])[A-Za-z\d\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]{8,}$', edit) is None:
            return False
        else:
            return True

    def resetFunc(self):
        pwdValidation = self.checkPWValid(self.newPwEdit.text())

        if not (self.newPwEdit.text() and self.newPwValidEdit.text()):
            QMessageBox.setStyleSheet(
                self, 'QMessageBox {color: rgb(120, 120, 120)}')
            QMessageBox.information(
                self, 'PIM agent', "입력하지 않은 정보가 있습니다.", QMessageBox.Yes)
        elif self.newPwEdit.text() != self.newPwValidEdit.text():
            QMessageBox.information(
                self, 'PIM agent', "새 비밀번호가 일치하지 않습니다.", QMessageBox.Yes)
        elif not pwdValidation:
            QMessageBox.information(
                self, 'PIM agent', "새 비밀번호가 규칙에 맞지 않습니다.", QMessageBox.Yes)
        else:
            resetPw(self.newPwEdit.text(), self.nickname)
            QMessageBox.information(
                self, 'PIM agent', "비밀번호가 재설정 되었습니다.", QMessageBox.Yes)
            self.close()

            preGuest = LoginClass(self.app)
            preGuest.exec()

    def setCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.prevPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.prevPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.prevPos = event.globalPos()

stInstance = singleton.SingleInstance()

app = QApplication(sys.argv)
initWindow = initClass(app)
initWindow.show()
app.exec_()
