import os
from PySide6.QtCore import Qt, QCoreApplication, QUrl, QThreadPool, Signal
#from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QWheelEvent
from laser import Laser
from builder import Builder
#from svgview import SVGView
from viewscene import ViewScene
from vobject import VObject
from lcconfig import LCConfig
from gconfig import GConfig
from vgraphicsscene import ViewGraphicsScene
import webbrowser
import resources

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Building Designer"

#class MainWindowUI(QObject):
class MainWindowUI(QMainWindow):
    
    load_complete_signal = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Threadpool to maintain responsiveness during load / export
        self.threadpool = QThreadPool()
        
        # Connect signal handler
        self.load_complete_signal.connect(self.load_complete)
        
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
        
        # Which scene shown in main window
        self.current_scene = 'front'
        
        self.gconfig = GConfig(status)
        self.builder = Builder(self.config)
        
        # Set default screensize (even if going to maximise afterwards)
        self.ui.resize(*self.gconfig.default_screensize)
        
        if self.gconfig.maximized == True:
            self.ui.showMaximized()
              
        # Create scenes ready for holding objects to view
        # Also create view scenes which are then used to draw the particular view on the scene
        self.scenes = {}
        self.view_scenes = {}
        for scene_name in self.config.allowed_views:
            #self.scenes[scene_name] = QGraphicsScene()
            self.scenes[scene_name] = ViewGraphicsScene(self)
            self.view_scenes[scene_name] = ViewScene(self.scenes[scene_name], self.builder, scene_name)
        
        # Default to front view
        self.ui.graphicsView.setScene(self.scenes[self.current_scene])

        # File Menu
        self.ui.actionOpen.triggered.connect(self.open_file_dialog)
        self.ui.actionExit.triggered.connect(QCoreApplication.quit)
        # Edit Menu
        # View Menu
        self.ui.actionZoom_Out.triggered.connect(self.zoom_out)
        self.ui.actionZoom_In.triggered.connect(self.zoom_in)
        # Help Menu
        self.ui.actionVisit_Website.triggered.connect(self.visit_website)
        
        self.ui.show()      


    def open_file_dialog(self):
        filename = QFileDialog.getOpenFileName(self.parent(), "Open building file", "", "Building file (*.json);;All (*.*)")
        print (f'Selected file {filename}')
        # possibly check for valid file
        if filename[0] == '':
            print ("No filename specified")
            return
        self.new_filename = filename[0]
        self.threadpool.start(self.file_open)

    def visit_website(self, s):
        webbrowser.open("https://www.penguintutor.com/projects/laser-cut-buildings")

    def edit_menu(self):
        pass
    
    # File open is called as a separate thread
    def file_open(self):
        print ("Loading file {self.new_filename}")
        # Prevent duplicate file opens (or saving when opening etc.)
        self.disable_file_actions()
        result = self.builder.load_file(self.new_filename)
        if result[0] == False:
            #Todo show error message
            print (f"Error {result[1]}")
        #print ("Building loaded")
        #print (f"Builder contents\n{self.builder.building.data}")
        # update load complete message - even if failed as otherwise load is locked
        self.load_complete_signal.emit()
        
    # Called from load_complete_signal after a file has been loaded
    def load_complete(self):
        # Reenable file actions
        self.enable_file_actions()
        print ("Updating GUI")
        # Todo update views
        self.update_all_views()

    # Whenever performing file action then disable other actions to prevent duplicates / conflicting
    def disable_file_actions(self):
        self.ui.actionOpen.setEnabled(False)
        
    def enable_file_actions(self):
        self.ui.actionOpen.setEnabled(True)
        
    def update_all_views (self):
        for scene_name in self.config.allowed_views:
            self.update_view (scene_name)
        
    def zoom_out (self):
        Laser.zl.zoom_out()
        self.update_view (self.current_scene)
        
    def zoom_in (self):
        Laser.zl.zoom_in()
        self.update_view (self.current_scene)
        
    # Updates each of the views by updating the scene
    def update_view (self, view_name):
        print (f"Updating scene {view_name}")
        self.view_scenes[view_name].update()
        # Show the main screen
        self.ui.graphicsView.show()
        
    def scene_scroll (self, in_out):
        print (f"Scroll received {in_out}")
