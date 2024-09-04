from PySide2.QtWidgets import QApplication
from mainwindow import MainWindow
import sys

class App(QApplication):
    def __init__ (self, args):
        super().__init__()
        

# Create QApplication instance 
app = App(sys.argv)

# Create a Qt widget - main window
window = MainWindow()
window.show()  # Show the window

#Start event loop
app.exec_()

# Application end