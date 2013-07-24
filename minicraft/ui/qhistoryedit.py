import webbrowser

from PyQt4 import QtCore, QtGui

from collections import deque

class QHistoryEdit(QtGui.QLineEdit):
    tabPressed = QtCore.pyqtSignal(unicode)
        
    def __init__(self,*arg,**kwargs):
        QtGui.QLineEdit.__init__(self,*arg,**kwargs)
        self.history = ["this","is","a","test"]
        self.index = 0

        self.model = QtGui.QStringListModel()
        
        completer = QtGui.QCompleter()
        completer.setModel(self.model)
        #completer.setSeparator(" ")
        
        self.setCompleter(completer)
        
        self.keymap = {
                       QtCore.Qt.Key_Up:self.previous_history,
                       QtCore.Qt.Key_Down:self.next_history,
                       QtCore.Qt.Key_Return:self.append_and_clear,
                       }
    def event(self,event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            print("Tab1")
            self.tabPressed.emit(self.text())
            return True
        return QtGui.QLineEdit.event(self,event)
    def tab_complete(self,list):
        self.model.setStringList(list)
        self.completer().complete()
    def next_history(self):
        self.index = max(self.index - 1, 0)
        if self.index > 0:
            self.setText(self.history[-self.index])
        else:
            self.clear()
    def previous_history(self):
        self.index = min(self.index + 1,len(self.history))
        if self.index > 0:
            self.setText(self.history[-self.index])
    def append_and_clear(self):
        self.history.append(self.text())
        self.history = self.history[-100:]
        self.index = 0
        self.clear()
    def keyPressEvent(self, event):
        QtGui.QLineEdit.keyPressEvent(self, event)
        if event.key() in self.keymap:
            self.keymap[event.key()]()