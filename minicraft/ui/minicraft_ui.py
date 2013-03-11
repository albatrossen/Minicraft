# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'minicraft_ui.ui'
#
# Created: Sat Mar  9 21:47:47 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(710, 599)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/main/icon.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setAnimated(True)
        MainWindow.setDocumentMode(False)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.chatlog = QPlainTextLog(self.centralwidget)
        self.chatlog.setFocusPolicy(QtCore.Qt.NoFocus)
        self.chatlog.setStyleSheet(_fromUtf8("QPlainTextEdit {\n"
"    background-color: black;\n"
"    color: white;\n"
"}"))
        self.chatlog.setUndoRedoEnabled(False)
        self.chatlog.setReadOnly(True)
        self.chatlog.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.chatlog.setObjectName(_fromUtf8("chatlog"))
        self.horizontalLayout.addWidget(self.chatlog)
        self.playerList = QtGui.QListWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.playerList.sizePolicy().hasHeightForWidth())
        self.playerList.setSizePolicy(sizePolicy)
        self.playerList.setMaximumSize(QtCore.QSize(160, 16777215))
        self.playerList.setObjectName(_fromUtf8("playerList"))
        self.horizontalLayout.addWidget(self.playerList)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.inputbox = QtGui.QLineEdit(self.centralwidget)
        self.inputbox.setMaxLength(100)
        self.inputbox.setObjectName(_fromUtf8("inputbox"))
        self.verticalLayout.addWidget(self.inputbox)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MiniCraft", None, QtGui.QApplication.UnicodeUTF8))

from qplaintextlog import QPlainTextLog
import resources_rc
