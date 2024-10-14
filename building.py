import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Qt, QCoreApplication, QUrl
from PySide6.QtUiTools import QUiLoader
from mainwindow import MainWindowUI
from scale import Scale
from zoom import Zoom
from laser import Laser


class App(QApplication):
    def __init__ (self, args):
        super().__init__()
        

# Scale for output - default to OO
sc = Scale("OO")
# Pass scale instance to laser class
Laser.sc = sc
# Zoom level for display
zl = Zoom()
Laser.zl = zl

# Create QApplication instance 
app = App(sys.argv)

# Create a Qt widget - main window
window = MainWindowUI()

#Start event loop
app.exec()

# Application end
