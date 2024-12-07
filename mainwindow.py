import os
from PySide6.QtCore import QCoreApplication, QThreadPool, Signal, QFileInfo
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QLabel, QTableWidget, QTableWidgetItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtUiTools import QUiLoader
from builder import Builder
from viewscene import ViewScene
from lcconfig import LCConfig
from gconfig import GConfig
from vgraphicsscene import ViewGraphicsScene
import webbrowser
import resources
from wallwindow import WallWindowUI

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Building Designer"

class MainWindowUI(QMainWindow):
    
    load_complete_signal = Signal()
    file_save_warning_signal = Signal()
    

    
    def __init__(self):
        super().__init__()
        
        # Threadpool to maintain responsiveness during load / export
        self.threadpool = QThreadPool()
        
        # Connect signal handler
        self.load_complete_signal.connect(self.load_complete)
        self.file_save_warning_signal.connect(self.file_save_warning)
        
        
        self.ui = loader.load(os.path.join(basedir, "mainwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = LCConfig()
        # How much we are zoomed in zoom (1 = 100%, 2 = 200%)
        self.zoom_level = 1
        
        # Used if need to send a status message (eg. pop-up warning)
        self.status_message = ""
        
        # Status is a dict used to pass information to gconfig at startup
        # Eg screensize
        status={}
        # Pass screensize to gconfig
        # Uses screen 0 which is normally current screen but may not be
        # Only used to set default size so doesn't matter if it's on a different
        # screen, but not such a good experience
        status['screensize'] = self.ui.screen().size().toTuple()
        
        self.filename = ""
        
        # Which scene shown in main window
        self.current_scene = 'front'
        
        self.gconfig = GConfig(status)
        self.builder = Builder(self.config)
        
        # Set default screensize (even if going to maximise afterwards)
        self.ui.resize(*self.gconfig.default_screensize)
        
        if self.gconfig.maximized == True:
            self.ui.showMaximized()
            
        # Set width for table column
        self.ui.infoTable.setColumnWidth(0, 100)
        self.ui.infoTable.setColumnWidth(1, 200)
              
        # Create scenes ready for holding objects to view
        # Also create view scenes which are then used to draw the particular view on the scene
        self.scenes = {}
        self.view_scenes = {}
        for scene_name in self.config.allowed_views:
            #self.scenes[scene_name] = QGraphicsScene()
            self.scenes[scene_name] = ViewGraphicsScene(self)
            self.view_scenes[scene_name] = ViewScene(self.scenes[scene_name], self.builder, self.gconfig, scene_name)
            # Signal for change in viewgraphicsscene (item selected / deselected)
            self.scenes[scene_name].focus_changed.connect(self.update_selected_view)
        
        # Default to front view
        self.ui.graphicsView.setScene(self.scenes[self.current_scene])

        # File Menu
        self.ui.actionOpen.triggered.connect(self.open_file_dialog)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_as_dialog)
        self.ui.actionExit.triggered.connect(QCoreApplication.quit)
        # Edit Menu
        self.ui.actionAdd_Wall.triggered.connect(self.add_wall)
        # View Menu
        self.ui.actionZoom_Out.triggered.connect(self.zoom_out)
        self.ui.actionZoom_In.triggered.connect(self.zoom_in)
        self.ui.actionFront.triggered.connect(self.view_front)
        self.ui.actionRight.triggered.connect(self.view_right)
        self.ui.actionRear.triggered.connect(self.view_rear)
        self.ui.actionLeft.triggered.connect(self.view_left)
        self.ui.actionTop.triggered.connect(self.view_top)
        self.ui.actionBottom.triggered.connect(self.view_bottom)
        # Help Menu
        self.ui.actionVisit_Website.triggered.connect(self.visit_website)
        
        # View buttons
        self.ui.frontViewButton.pressed.connect(self.view_front)
        self.ui.frontViewImageButton.pressed.connect(self.view_front)
        self.ui.rightViewButton.pressed.connect(self.view_right)
        self.ui.rightViewImageButton.pressed.connect(self.view_right)
        self.ui.rearViewButton.pressed.connect(self.view_rear)
        self.ui.rearViewImageButton.pressed.connect(self.view_rear)
        self.ui.leftViewButton.pressed.connect(self.view_left)
        self.ui.leftViewImageButton.pressed.connect(self.view_left)
        self.ui.topViewButton.pressed.connect(self.view_top)
        self.ui.topViewImageButton.pressed.connect(self.view_top)
        self.ui.bottomViewButton.pressed.connect(self.view_bottom)
        self.ui.bottomViewImageButton.pressed.connect(self.view_bottom)
        
        # Action buttons
        self.ui.addWallButton.pressed.connect(self.add_wall)
        
        self.ui.show()
        
        # Set to none, only create when needed and can check if it's created yet
        self.wall_window = None
        #self.wall_window = WallWindowUI()


    def open_file_dialog(self):
        filename = QFileDialog.getOpenFileName(self.parent(), "Open building file", "", "Building file (*.json);;All (*.*)")
        print (f'Selected file {filename}')
        # possibly check for valid file
        if filename[0] == '':
            print ("No filename specified")
            return
        self.ui.statusbar.showMessage ("Loading "+filename[0])
        self.new_filename = filename[0]
        self.threadpool.start(self.file_open)
        
    # Note save_file is called from the UI
    # file_save is then called subsequently (typically in a threadpool)
    # to perform the actual save operation
    def save_file(self):
        # If no existing filename then open dialog
        if (self.filename == ""):
            self.save_as_dialog()
            # Dialog is standalone so finished at this point
            return
        # reach here then saving existing file
        # No need to verify overwrite, just save
        # Use new_filename for save as well as leaving in self.filename
        self.new_filename = self.filename
        self.ui.statusbar.showMessage ("Saving "+self.new_filename)
        self.threadpool.start(self.file_save)
                    
    # Called from Save as, or if no existing filename
    # Prompt user for file to safe as
    def save_as_dialog(self):
        filename = QFileDialog.getSaveFileName(self, "Save building file", "", "Building file (*.json);;All (*.*)", "Building file (*.json)", QFileDialog.DontConfirmOverwrite)
        print (f"Filename is {filename}")
        this_filename = filename[0]
        # If no suffix/extension then add here
        # Basic check for extension using os.path.splitext
        file_and_ext = os.path.splitext(this_filename)
        # If there is an extension then just continue (don't check it matches), but if not then add .json
        if (file_and_ext[1] == ""):
            this_filename += ".json"
        # Check if file exists
        file_info = QFileInfo(this_filename)
        # Due to problem with getSaveFilename and suffix need to create own message box
        # Otherwise whilst the dialog box will check for file replace it will provide filename with suffix added, but only
        # check filename without suffix.
        if file_info.exists():
            # Confirm with user to delete
            confirm_box = QMessageBox.question(self, "File already exists", f"The file:\n{this_filename} already exists.\n\nDo you want to replace this file?")
            if confirm_box == QMessageBox.Yes:
                print ("Yes replace file")
            else:
                print ("No do not replace")
                return
        
        if this_filename == '':
            print ("No filename specified for save")
            return
        self.new_filename = this_filename

        self.ui.statusbar.showMessage ("Saving as "+self.new_filename)
        # Reach here then it's saving in a new file (not overwrite)
        self.threadpool.start(self.file_save)

    # Performs the actual save (normally triggered in a threadpool)
    def file_save(self):
        print (f"Saving file {self.new_filename}")
        # Todo implement this
        success = self.builder.save_file(self.new_filename)
        # If successful then confirm new filename
        if success[0] == True:
            self.filename = self.new_filename
        # If not then give an error message - need to pass back to GUI thread
        else:
            self.status_message = f"Unable to save {self.new_filename}.\n\nError: {success[1]}"
            self.file_save_warning_signal.emit()
            
    def file_save_warning(self):
        QMessageBox.warning(self, "File save error", self.status_message, QMessageBox.Ok)
        

    def visit_website(self, s):
        webbrowser.open("https://www.penguintutor.com/projects/laser-cut-buildings")

    def edit_menu(self):
        pass
    
    # File open is called as a separate thread
    def file_open(self):
        print (f"Loading file {self.new_filename}")
        # Prevent duplicate file opens (or saving when opening etc.)
        self.disable_file_actions()
        result = self.builder.load_file(self.new_filename)
        if result[0] == False:
            #Todo show error message
            print (f"Error {result[1]}")
            self.ui.statusbar.showMessage ("Error "+result[1])
        #print ("Building loaded")
        #print (f"Builder contents\n{self.builder.building.data}")
        else:
            self.filename = self.new_filename
            #self.ui.statusbar.showMessage ("Loaded "+self.filename)
            self.update_status()
        # update load complete message - even if failed as otherwise load is locked
        self.load_complete_signal.emit()
        
    # Called from load_complete_signal after a file has been loaded
    def load_complete(self):
        # Reenable file actions
        self.enable_file_actions()
        print ("Updating GUI")
        self.update_all_views()
        #print (f"Items {self.view_scenes[self.current_scene].scene.items()}")
        #print (f"Group {self.view_scenes[self.current_scene].obj_views[0].item_group}")
        #print (f"Group Items {self.view_scenes[self.current_scene].obj_views[0].item_group.items()}")

    # Whenever performing file action then disable other file actions to prevent duplicates / conflicting
    def disable_file_actions(self):
        self.ui.actionOpen.setEnabled(False)
        
    def enable_file_actions(self):
        self.ui.actionOpen.setEnabled(True)
        
    def update_all_views (self):
        for scene_name in self.config.allowed_views:
            self.update_view (scene_name)
        
    def zoom_out (self):
        # Minimum zoom is 0.125 - actually two values for scale, but just look at x
        #current_scale = self.ui.graphicsView.transform().m11()
        #if current_scale <= 0.125:
        if self.zoom_level <= 0.25:
            return
        else:
            self.zoom_level -= 0.25
        # Otherwise scale by 1/2 size
        self.ui.graphicsView.resetTransform()
        self.ui.graphicsView.scale(self.zoom_level, self.zoom_level)
        self.update_status()
        #print (f"Transform {self.ui.graphicsView.transform().m11()}")
        
    def zoom_in (self):
        # Maximum zoom is 64 - actually two values for scale, but just look at x
        #current_scale = self.ui.graphicsView.transform().m11()
        #if current_scale >= 64:
        if self.zoom_level >= 10:
            return
        else:
            self.zoom_level += 0.25        
        # Otherwize zoom in by twice current
        self.ui.graphicsView.resetTransform()
        self.ui.graphicsView.scale(self.zoom_level, self.zoom_level)
        self.update_status()
        #print (f"Transform {self.ui.graphicsView.transform().m11()}")

    # Update statusbar.
    # If no message then show standard message otherwise override
    # Eg. if loading then that is shown instead
    def update_status(self, message=None):
        if message == None:
            message = f"File {self.filename} Zoom: {int(self.zoom_level * 100)} %"
        self.ui.statusbar.showMessage (message)
            
        
    # Updates each of the views by updating the scene
    def update_view (self, view_name):
        #print (f"Updating scene {view_name}")
        self.view_scenes[view_name].update()
        # Show the main screen
        self.ui.graphicsView.show()
        
    #def scene_scroll (self, in_out):
    #    print (f"Scroll received {in_out}")
        
    def view_front (self):
        self.change_scene('front')
    def view_right (self):
        self.change_scene('right')
    def view_rear (self):
        self.change_scene('rear')
    def view_left (self):
        self.change_scene('left')
    def view_top (self):
        self.change_scene('top')
    def view_bottom (self):
        self.change_scene('bottom')

    def change_scene (self, new_scene):
        self.current_scene = new_scene
        self.view_scenes[new_scene].update()
        self.ui.graphicsView.setScene(self.scenes[self.current_scene])
        self.ui.graphicsView.show()

    # Add new wall dialog
    def add_wall (self):
        if self.wall_window == None:
            self.wall_window = WallWindowUI(self, self.config, self.gconfig, self.builder)
        else:
            self.wall_window.show()
        #print ("Wall window launched")
        
    # Update based on selection in viewgraphicsscene
    def update_selected_view (self, selected_items):
        # Selection are items selected
        # For normal scenes these are groups (because each wall is composed of groups of items
        # which are in <ObjView>.item_group
        # To know which are selected need to query each of the ObjViews in the current <ViewScene>
        # First check if some items are selection
        #print (f"Update view {selected_items}")
        if selected_items != None:
            selected_objs = []
            # Call get info to find information on what is selected
            for this_obj in selected_items:
                selected_objs.append(self.view_scenes[self.current_scene].get_obj_from_obj_view(this_obj))
                #print (f"Obj selected: {obj_info}")
                #print (f"Object type: {obj_info.type}, name: {obj_info.name}")
            # reset all table rows
            self.ui.infoTable.setRowCount(0)
            if (len(selected_objs) > 1):
                #print ("multi")
                #self.ui.infoTable.setHorizontalHeaderLabels([f"{len(selected_objs)} selected"])
                self.ui.infoLabel.setText(f"{len(selected_objs)} objects selected")
                self.ui.infoTable.setRowCount(len(selected_objs))
                for i in range (0, len(selected_objs)):
                    self.ui.infoTable.setItem(i,0, QTableWidgetItem(f"Object {i}"))
                    self.ui.infoTable.setItem(i,1, QTableWidgetItem(f"{selected_objs[0].type} - {selected_objs[i].name}"))
                    
                #for i in range (0, len(selected_obs))
            elif (len(selected_objs) == 1):
                self.ui.infoLabel.setText(f"One object selected")
                self.ui.infoTable.setRowCount(2)
                self.ui.infoTable.setItem(0,0, QTableWidgetItem("Name"))
                self.ui.infoTable.setItem(0,1, QTableWidgetItem(selected_objs[0].name))
                self.ui.infoTable.setItem(1,0, QTableWidgetItem("Type"))
                self.ui.infoTable.setItem(1,1, QTableWidgetItem(selected_objs[0].type))
            else:
                self.ui.infoLabel.setText(f"No objects selected")
                #self.ui.infoTable.setVerticalHeaderLabels(["", ""])
        else:
            #print ("Setting none selected")
            self.ui.infoLabel.setText(f"No objects selected")
            #self.ui.infoTable.setHorizontalHeaderLabels(["None selected"])
            #self.ui.infoTable.setVerticalHeaderLabels(["", ""])
