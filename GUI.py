import sys
import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import Qt

from Run import *

init_form_class = uic.loadUiType("initGUI.ui")[0]
login_form_class = uic.loadUiType("loginGUI.ui")[0]


class LoginClass(QDialog, login_form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("windowIcon.png"))

        self.id = ""
        self.password = ""

        self.idEdit: QLineEdit
        self.passEdit: QLineEdit
        self.loginBtn: QPushButton

        self.loginBtn.clicked.connect(self.btnFunction)

    def getId(self):
        return self.id

    def btnFunction(self):
        self.id = self.idEdit.text()
        self.password = self.passEdit.text()

        if(self.id == 'test' and self.password == 'test'):
            self.hide()

            mainWindow = InitClass(self)
            mainWindow.exec()

            self.idEdit.setText("")
            self.passEdit.setText("")
            self.show()

            # 49 ~ 54 line thread 필요
            initCheck()

            beginTimer = time.time()

            while(not mainWindow.breakPoint):
                run(beginTimer)


class InitClass(QDialog, init_form_class):

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.titleLabel: QLabel
        self.logoutBtn: QPushButton
        self.breakPoint = False

        self.setWindowIcon(QIcon("windowIcon.png"))

        self.titleLabel.setText(loginWindow.getId() + " 님")
        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.logoutBtn.clicked.connect(self.logout)

    def logout(self):
        self.breakPoint = True
        self.close()


app = QApplication(sys.argv)
loginWindow = LoginClass()
loginWindow.show()
app.exec_()
