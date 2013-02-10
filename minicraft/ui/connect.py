# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'connect.ui'
#
# Created: Sun Feb 10 22:12:45 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ConnectWindow(object):
    def setupUi(self, ConnectWindow):
        ConnectWindow.setObjectName(_fromUtf8("ConnectWindow"))
        ConnectWindow.resize(216, 137)
        self.verticalLayout = QtGui.QVBoxLayout(ConnectWindow)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.l_servername = QtGui.QLabel(ConnectWindow)
        self.l_servername.setObjectName(_fromUtf8("l_servername"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.l_servername)
        self.servername = QtGui.QLineEdit(ConnectWindow)
        self.servername.setObjectName(_fromUtf8("servername"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.servername)
        self.l_username = QtGui.QLabel(ConnectWindow)
        self.l_username.setObjectName(_fromUtf8("l_username"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.l_username)
        self.username = QtGui.QLineEdit(ConnectWindow)
        self.username.setObjectName(_fromUtf8("username"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.username)
        self.l_password = QtGui.QLabel(ConnectWindow)
        self.l_password.setObjectName(_fromUtf8("l_password"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.l_password)
        self.password = QtGui.QLineEdit(ConnectWindow)
        self.password.setEchoMode(QtGui.QLineEdit.PasswordEchoOnEdit)
        self.password.setObjectName(_fromUtf8("password"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.password)
        self.verticalLayout.addLayout(self.formLayout)
        self.status = QtGui.QLabel(ConnectWindow)
        self.status.setObjectName(_fromUtf8("status"))
        self.verticalLayout.addWidget(self.status)
        self.buttonBox = QtGui.QDialogButtonBox(ConnectWindow)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ConnectWindow)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ConnectWindow.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ConnectWindow.reject)
        QtCore.QMetaObject.connectSlotsByName(ConnectWindow)

    def retranslateUi(self, ConnectWindow):
        ConnectWindow.setWindowTitle(QtGui.QApplication.translate("ConnectWindow", "Connect to Server", None, QtGui.QApplication.UnicodeUTF8))
        self.l_servername.setText(QtGui.QApplication.translate("ConnectWindow", "Server", None, QtGui.QApplication.UnicodeUTF8))
        self.l_username.setText(QtGui.QApplication.translate("ConnectWindow", "Username", None, QtGui.QApplication.UnicodeUTF8))
        self.l_password.setText(QtGui.QApplication.translate("ConnectWindow", "Password", None, QtGui.QApplication.UnicodeUTF8))

