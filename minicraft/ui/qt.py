# coding=utf8
import getpass, time, re, sys, os
import ConfigParser

from PyQt4 import QtCore, QtGui
import keyring

from minicraft.packets import ChatMessage, TabComplete
from minicraft.protocol import MineCraftConnection, Session, FailedLogin
from minicraft.ui.minicraft_ui import Ui_MainWindow
from minicraft.ui.connect import Ui_ConnectWindow
from minicraft.colorhtml import format_json, strip_codes

class MainWindow(QtGui.QMainWindow):
	chatmessage = QtCore.pyqtSignal(str)
	tabcomplete = QtCore.pyqtSignal(str)
	completeprefix = None

	def __init__(self,parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.ui.chatlog.document().setDefaultStyleSheet("a{color:inherit;}")
	def on_inputbox_returnPressed(self):
		msg = self.ui.inputbox.text()
		if msg[:3] == "/p ":
			self.ui.chatlog.appendPlainText(repr(eval(str(msg[3:]))))
		else:
			self.chatmessage.emit(msg)
	def on_inputbox_tabPressed(self,msg = None):
		if not self.completeprefix:
			self.tabcomplete.emit(msg)
			f = str(msg)
			i = f.rfind(" ")
			self.completeprefix = f[:i+1] if i >= 0 else ""
	def send_tab(self):
		msg = self.ui.inputbox.text()
		self.tabcomplete.emit(msg)
	def on_tab_complete(self,completions):
		if self.completeprefix is not None:
		    complete_list = [self.completeprefix + x for x in unicode(completions).split("\0")]
		    print(complete_list)
		    self.ui.inputbox.tab_complete(complete_list)
		self.completeprefix = None
	def on_player_list_add(self,player):
		stripped_player = strip_codes(player)
		if not self.ui.playerList.findItems(stripped_player,QtCore.Qt.MatchExactly):
			self.ui.playerList.addItem(strip_codes(player))

	def on_player_list_remove(self,player):
		stripped_player = strip_codes(player)
		for i in range( self.ui.playerList.count() ):
			if self.ui.playerList.item(i).text() == stripped_player:
				self.ui.playerList.takeItem(i)
				return

	def on_chatmessage(self,msg):
		self.ui.chatlog.appendHtml(format_json(unicode(msg)))

	def connect(self, session, host):
		self.connection=QtConnection()
		self.connection.start_session(session,str(host))
		self.connection.chatmessage.connect(self.on_chatmessage)
		self.connection.player_list_add.connect(self.on_player_list_add)
		self.connection.player_list_remove.connect(self.on_player_list_remove)
		self.connection.tabComplete.connect(self.on_tab_complete)

		self.tabcomplete.connect(self.connection.send_tabcomplete)
		self.chatmessage.connect(self.connection.send_message)
		self.connection.start()

class LoginWindow(QtGui.QDialog):
	connecting = False
	session_ready = QtCore.pyqtSignal(Session,str)
	config_filename = os.path.join(os.path.dirname(sys.argv[0]),'minicraft.cfg')
	sound = QtGui.QSound('notify.wav')

	def __init__(self,parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_ConnectWindow()
		self.ui.setupUi(self)
		self.config = ConfigParser.RawConfigParser()
		self.config.read(self.config_filename)
		try:
			username = self.config.get('Minicraft','username')
			self.ui.username.setText(username)
			server = self.config.get('Minicraft','server')
			self.ui.servername.setText(server)
			try:
				password = keyring.get_password("Minicraft",username)
				self.ui.password.setText(password)
			except:
				pass
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
	def login_fail(self):
		#QtGui.QSound.play('notify.wav')
		#self.sound.play()
		#print("playing sound")
		pass
	def login_ok(self,session):
		server = str(self.ui.servername.text())
		self.config.set('Minicraft','server',server)
		self.config.set('Minicraft','username',session.username)
		try:
			keyring.set_password("Minicraft",session.username.encode('utf8'),self.thread.password.encode('utf8'))
		except:
			pass
		with open(self.config_filename, 'wb') as configfile:
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

	chatmessage = QtCore.pyqtSignal(unicode)
	player_list_add = QtCore.pyqtSignal(str)
	player_list_remove = QtCore.pyqtSignal(str)
	tabComplete = QtCore.pyqtSignal(unicode)

	def run(self):
		self.recv()
	def onChatMessage(self,packet):
		self.chatmessage.emit(packet.message)
	def onDisconnect(self,packet):
		self.chatmessage.emit(u"§7Disconnected: §c" + packet.reason)
	def send_message(self,msg):
		self.send(ChatMessage(unicode(msg[:100])))
	def send_tabcomplete(self,msg):
		self.send(TabComplete(unicode(msg[:100])))		
	def onPlayerListItem(self,packet):
		if packet.online:
			self.player_list_add.emit(packet.player_name)
		else:
			self.player_list_remove.emit(packet.player_name)
	def onTabComplete(self,packet):
		print(repr(packet.text))
		self.tabComplete.emit(packet.text)

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
