import sys
import time
import re

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *

from Run import initCheck, run
from DB_setting import getLoginData, checkIDUnique, checkNicknameUnique, setMembership, getID, getPW

login_form_class = uic.loadUiType("loginGUI.ui")[0]
run_form_class = uic.loadUiType("runGUI.ui")[0]
join_form_class = uic.loadUiType("joinGUI.ui")[0]
find_form_class = uic.loadUiType("findGUI.ui")[0]


class Thread(QThread):

    # 초기화 메서드 구현
    def __init__(self, nickname):
        super().__init__()
        self.breakPoint = False
        self.nickname = nickname

    def run(self):
        initCheck()
        beginTimer = time.time()

        while(not self.breakPoint):
            run(beginTimer, self.nickname)
        # 쓰레드로 동작시킬 함수 내용 구현

    def stop(self):
        self.breakPoint = True
        self.quit()
        self.wait(3000)

# 로그인 gui


class LoginClass(QDialog, login_form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("windowIcon.png"))

        self.id = ""
        self.password = ""
        self.nickname = ""

        self.idEdit: QLineEdit
        self.pwdEdit: QLineEdit
        self.loginBtn: QPushButton
        self.joinBtn: QPushButton
        self.findBtn: QPushButton

        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.loginBtn.clicked.connect(self.btnLoginFunc)
        self.joinBtn.clicked.connect(self.btnJoinFunc)
        self.findBtn.clicked.connect(self.btnFindFunc)

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
            self.hide()

            mainWindow = RunClass(self)
            mainWindow.setNickname(self.nickname)
            mainWindow.setThread()
            mainWindow.exec()

            self.idEdit.setText("")
            self.pwdEdit.setText("")
            self.show()
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

    def __init__(self, parent=None):
        super().__init__()
        self.nickname = ""

        self.setupUi(self)
        self.titleLabel: QLabel
        self.visitCheckBox:QCheckBox
        self.downloadCheckBox:QCheckBox
        self.bookmarkCheckBox:QCheckBox
        self.autoFormCheckBox:QCheckBox
        self.cookieCheckBox:QCheckBox
        self.cacheCheckBox:QCheckBox
        self.sessionCheckBox:QCheckBox
        self.setDBBtn:QPushButton
        self.logoutBtn: QPushButton

        self.setWindowIcon(QIcon("windowIcon.png"))

        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.setDBBtn.clicked.connect(self.setDB)
        self.logoutBtn.clicked.connect(self.logout)
    
    def setNickname(self, nickname):
        self.nickname = nickname
        self.titleLabel.setText(nickname + " 님")

    def setThread(self):
        # start 메소드 호출 -> 자동으로 run 메소드 호출
        self.daemonThread = Thread(self.nickname)
        self.daemonThread.start()

    def setDB(self):
        print("setDB clicked")

    def logout(self):
        self.daemonThread.stop()
        self.close()


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
loginWindow = LoginClass()
loginWindow.show()
app.exec_()
