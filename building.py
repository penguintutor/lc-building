import sys
import os
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QObject
from PySide2.QtCore import Qt, QCoreApplication, QUrl
from PySide2.QtUiTools import QUiLoader
from mainwindow import MainWindowUI




#class MainUI(QObject):
#    def __init__(self):
#        super().__init__()
#        self.ui = loader.load(os.path.join(basedir, "mainwindow.ui"), None)
#        self.ui.setWindowTitle("LC Building")
#        self.ui.show()
#        
#        self.ui.actionExit.triggered.connect(QCoreApplication.quit)
        


class App(QApplication):
    def __init__ (self, args):
        super().__init__()
        

# Create QApplication instance 
app = App(sys.argv)

# Create a Qt widget - main window
window = MainWindowUI()
#window.show()  # Show the window
#ui = MainUI()

#Start event loop
app.exec_()

# Application end