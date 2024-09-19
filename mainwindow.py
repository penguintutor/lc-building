import os
from PySide6.QtCore import Qt, QCoreApplication, QUrl
#from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtUiTools import QUiLoader
from builder import Builder
from lcconfig import LCConfig
from gconfig import GConfig
import webbrowser
import resources

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Building Designer"

class MainWindowUI(QObject):
    def __init__(self):
        super().__init__()
        self.ui = loader.load(os.path.join(basedir, "mainwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = LCConfig()
        
        # Status is a dict used to pass information to gconfig at startup
        # Eg screensize
        status={}
        # Pass screensize to gconfig
        # Uses screen 0 which is normally current screen but may not be
        # Only used to set default size so doesn't matter if it's on a different
        # screen, but not such a good experience
        status['screensize'] = self.ui.screen().size().toTuple()
        
        self.gconfig = GConfig(status)
        self.builder = Builder(self.config)
        
        # Set default screensize (even if going to maximise afterwards)
        self.ui.resize(*self.gconfig.default_screensize)
        
        if self.gconfig.maximized == True:
            self.ui.showMaximized()
            
        self.scene = QGraphicsScene()
        self.scene.addText("Hello, world!")
        
        #addItem
        #QGraphicsSvgItem
        
        
        self.ui.graphicsView.setScene(self.scene)
#view = QGraphicsView(scene)
#view.show()
      
        self.ui.actionExit.triggered.connect(QCoreApplication.quit)
        self.ui.actionVisit_Website.triggered.connect(self.visit_website)
        
        self.ui.show()      


    def visit_website(self, s):
        webbrowser.open("https://www.penguintutor.com/projects/laser-cut-buildings")



    def edit_menu(self):
        pass

