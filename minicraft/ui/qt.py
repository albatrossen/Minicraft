# coding=utf8
import getpass, time, re
import ConfigParser

from PyQt4 import QtCore, QtGui
import keyring

from minicraft.packets import ChatMessage
from minicraft.protocol import MineCraftConnection, Session, FailedLogin
from minicraft.ui.minicraft_ui import Ui_MainWindow
from minicraft.ui.connect import Ui_ConnectWindow
from minicraft.colorhtml import convert_to_html

class MainWindow(QtGui.QMainWindow):
	chatmessage = QtCore.pyqtSignal(str)

	def __init__(self,parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
	def on_inputbox_returnPressed(self):
		msg = self.ui.inputbox.text()
		if msg[:3] == "/p ":
			self.ui.chatlog.appendPlainText(repr(eval(str(msg[3:]))))
		else:
			self.chatmessage.emit(msg)
			self.ui.inputbox.clear()

	def on_chatmessage(self,msg):
		self.ui.chatlog.appendHtml(convert_to_html(unicode(msg)))

	def connect(self, session, host):
		self.connection=QtConnection()
		self.connection.start_session(session,str(host))
		self.connection.chatmessage.connect(self.on_chatmessage)
		self.chatmessage.connect(self.connection.send_message)
		self.connection.start()

class LoginWindow(QtGui.QDialog):
	connecting = False
	session_ready = QtCore.pyqtSignal(Session,str)
	def __init__(self,parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_ConnectWindow()
		self.ui.setupUi(self)
		self.config = ConfigParser.RawConfigParser()
		self.config.read('minicraft.cfg')
		try:
			username = self.config.get('Minicraft','username')
			server = self.config.get('Minicraft','server')
			password = keyring.get_password("Minicraft",username)
			self.ui.username.setText(username)
			self.ui.servername.setText(server)
			if password:
				self.ui.password.setText(password)
		except ConfigParser.NoSectionError:
			self.config.add_section('Minicraft')
		except ConfigParser.NoOptionError:
			pass
	def accept(self):
		if self.connecting:
			return
		self.connecting = True
		self.ui.status.setText(self.tr("Connecting"))
		self.thread = QtSession(unicode(self.ui.username.text()),unicode(self.ui.password.text()))
		self.thread.login_ok.connect(self.login_ok)
		self.thread.login_fail.connect(self.login_fail)
		self.thread.start()
	def login_fail(self, msg):
		self.ui.status.setText(msg)
		self.connecting = False
	def login_ok(self,session):
		server = str(self.ui.servername.text())
		self.config.set('Minicraft','server',server)
		self.config.set('Minicraft','username',session.username)
		keyring.set_password("Minicraft",session.username.encode('utf8'),self.thread.password.encode('utf8'))
		with open('minicraft.cfg', 'wb') as configfile:
		    self.config.write(configfile)
		self.close()
		self.session_ready.emit(session,server)
		

class QtSession(QtCore.QThread):
	login_ok = QtCore.pyqtSignal(Session)
	login_fail = QtCore.pyqtSignal(str)
	def __init__(self,username,password,parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.username = username
		self.password = password
		self.session = Session()
	def run(self):
		try:
			self.session.login(self.username,self.password)
		except FailedLogin as e:
			self.login_fail.emit(str(e))
			return
		self.login_ok.emit(self.session)


class QtConnection(QtCore.QThread,MineCraftConnection):
	def __init__(self,parent=None):
		QtCore.QThread.__init__(self,parent)
		MineCraftConnection.__init__(self)
	control_matcher = re.compile("\xa7.")
	chatmessage = QtCore.pyqtSignal(unicode)
	def run(self):
		self.recv()
	def onChatMessage(self,packet):
		self.chatmessage.emit(packet.message)
	def onDisconnect(self,packet):
		self.chatmessage.emit(u"§7Disconnected: §c" + packet.reason)
	def send_message(self,msg):
		self.send(ChatMessage(unicode(msg[:100])))

class QtUI():
	def run(self,*argv):
		app = QtGui.QApplication(list(argv))
		mainwindow = MainWindow()
		mainwindow.show()

		connectwindow = LoginWindow(mainwindow)
		connectwindow.show()

		connectwindow.session_ready.connect(mainwindow.connect)
		
		#session = Session('faua',getpass.getpass("Password:"))
		#mainwindow.show()
		return app.exec_()
