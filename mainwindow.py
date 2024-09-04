from PySide2.QtCore import Qt, QCoreApplication, QUrl
from PySide2.QtGui import QPixmap, QIcon, QPainter, QPen, QColor, QBrush, QFontMetrics
from PySide2.QtWidgets import (
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QMenu,
    QWidget,
    QToolBar,
    QStatusBar,
    QTabWidget,
    QFrame,
    QAction
)
from PySide2.QtWebEngineWidgets import QWebEngineView
from builder import Builder
from config import Config



app_title = "Building Designer"

# Subclass QMainWindow as application main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.builder = Builder(self.config)
        
#        self.config = Config()
# Use below to set window maximized
#        self.setWindowState(Qt.WindowMaximized)
        
        self.setWindowTitle(app_title)
        
        # Get screen size - allows to auto size the image if enabled
        # Only looks at screen 0, may not be the screen this is running on
        screen_size = self.screen().size().toTuple()
