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
from lcconfig import LCConfig
from gconfig import GConfig


app_title = "Building Designer"

# Subclass QMainWindow as application main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = LCConfig()
        
        # Status is a dict used to pass information to gconfig at startup
        # Eg screensize
        status={}
        # Pass screensize to gconfig
        # Uses screen 0 which is normally current screen but may not be
        # Only used to set default size so doesn't matter if it's on a different
        # screen, but not such a good experience
        status['screensize'] = self.screen().size().toTuple()
        
        self.gconfig = GConfig(status)
        self.builder = Builder(self.config)
        
        # Set default screensize (even if going to maximise afterwards)
        self.resize(*self.gconfig.default_screensize)
        
        if self.gconfig.maximized == True:
            #self.setWindowState(Qt.WindowMaximized)
            self.showMaximized()          
            
        
        self.setWindowTitle(app_title)
        
        # Get screen size - allows to auto size the image if enabled
        # Only looks at screen 0, may not be the screen this is running on
        #screen_size = self.screen().size().toTuple()


        # Actions
        edit_action = QAction(QIcon(), "Edit", self)
        edit_action.triggered.connect(self.edit_menu)
        
        quit_action = QAction(QIcon(), "Exit", self)
        quit_action.triggered.connect(QCoreApplication.quit)
        
        penguin_action = QAction(QIcon("icon01.png"), "Visit website", self)
        penguin_action.setStatusTip("Visit website")
        penguin_action.triggered.connect(self.visit_website)

        # Traditional pull-down menus
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_menu.addAction(quit_action)
        
        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(edit_action)
           
        help_menu = menu.addMenu("&Help")
        help_menu.addAction(penguin_action)
        
        
        self.show()
        


    def visit_website(self, s):
        #Todo - open website
        #print("click", s)
        pass


    def edit_menu(self):
        pass