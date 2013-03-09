import webbrowser

from PyQt4 import QtCore, QtGui

class QPlainTextLog(QtGui.QPlainTextEdit):
	def mouseReleaseEvent(self,e):
		cursor = self.textCursor()
		if cursor.selectionStart() != cursor.selectionEnd():
			self.copy()
		else:
			link = self.anchorAt(e.pos())
			if link:
				webbrowser.open(self.anchorAt(e.pos()))
		cursor.clearSelection()
		self.setTextCursor(cursor)
		super(QPlainTextLog,self).mouseReleaseEvent(e)