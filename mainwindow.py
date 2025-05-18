import os
from PySide6.QtCore import Qt, QCoreApplication, QThreadPool, Signal, QFileInfo
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QProgressDialog, QLabel, QComboBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QKeyEvent
from vgraphicsscene import ViewGraphicsScene
import webbrowser
import copy
from builder import Builder
from viewscene import ViewScene
from editscene import EditScene
from lcconfig import LCConfig
from gconfig import GConfig
from wallwindow import WallWindowUI
from texturewindow import TextureWindowUI
from addfeaturewindow import AddFeatureWindowUI
from featureposwindow import FeaturePosWindowUI
from interlockingwindow import InterlockingWindowUI
from history import History
from scale import Scale
from laser import Laser
from interlocking import Interlocking

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Building Designer"

class MainWindowUI(QMainWindow):
    
    load_complete_signal = Signal()
    file_save_warning_signal = Signal()
    progress_update_signal = Signal(int)
    update_views_signal = Signal()
    undo_menu_signal = Signal(str)
    redo_menu_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
                
        self.config = LCConfig()
        # How much we are zoomed in zoom (1 = 100%, 2 = 200%)
        self.zoom_level = 1.0
        
        default_scale = "OO"
        
        # Scale for output - default to OO
        self.sc = Scale(default_scale)
        # Pass scale instance to laser class
        Laser.sc = self.sc
        
        # Use scale to apply reverse scale to actual material_thickness
        material_thickness = self.config.wall_width
        self.scale_material = self.sc.reverse_scale_convert(material_thickness)
        # Set material thickness for Interlocking (class variable)
        Interlocking.material_thickness = self.scale_material
        
        # Threadpool to maintain responsiveness during load / export
        self.threadpool = QThreadPool()

        self.ui = loader.load(os.path.join(basedir, "mainwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        # Progress dialog window (create when required)
        self.progress_window = None
        
        self.history = History(self)

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
        if self.gconfig.debug > 0:
            print ("Debug - Create Main Window")
        self.builder = Builder(self.config, self.threadpool, self)
        
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
            self.view_scenes[scene_name] = ViewScene(self, self.scenes[scene_name], self.builder, self.gconfig, scene_name)
            # Signal for change in viewgraphicsscene (item selected / deselected)
            self.scenes[scene_name].focus_changed.connect(self.update_selected_view)

        # One more scene which is called "walledit" which is used to edit a particular wall
        self.scenes["walledit"] = ViewGraphicsScene(self)
        self.view_scenes['walledit'] = EditScene(self, self.scenes["walledit"], self.builder, self.gconfig, "walledit")
        self.scenes["walledit"].focus_changed.connect(self.update_selected_view)
        
        # Default to front view
        self.ui.graphicsView.setScene(self.scenes[self.current_scene])

        ### Additional Windows 
        # Set to none, only create when needed and can check if it's created yet
        self.wall_window = None
        self.texture_window = None
        self.add_feature_window = None
        self.interlocking_window = None
        self.feature_pos_window = None

        ### Additional GUI configuration
        # Add signal handlers
        self.load_complete_signal.connect(self.load_complete)
        self.file_save_warning_signal.connect(self.file_save_warning)
        self.progress_update_signal.connect(self.update_progress_dialog)
        self.update_views_signal.connect(self.update_all_views)
        self.undo_menu_signal.connect(self.update_undo_menu)
        self.redo_menu_signal.connect(self.update_redo_menu)

        # File Menu
        self.ui.actionNew.triggered.connect(self.file_new)
        self.ui.actionOpen.triggered.connect(self.open_file_dialog)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_as_dialog)
        self.ui.actionExport.triggered.connect(self.export_dialog)
        self.ui.actionExit.triggered.connect(self.quit_app)
        #self.ui.actionExit.triggered.connect(self.closeEvent)
        
        # Edit Menu
        self.ui.actionUndo.triggered.connect(self.undo)
        self.ui.actionRedo.triggered.connect(self.redo)
        # Undo and Redo are disabled until have some history
        self.ui.actionUndo.setEnabled(False)
        self.ui.actionRedo.setEnabled(False)
        self.ui.actionAdd_Wall.triggered.connect(self.add_wall)
        self.ui.actionWallTexture.triggered.connect(self.texture_properties)
                
        # Feature Menu (this menu is only shown when it edit mode)
        self.ui.actionAddFeature.triggered.connect(self.add_feature)
        self.ui.actionDeleteFeature.triggered.connect(self.delete_feature)
        self.ui.actionPositionFeature.triggered.connect(self.feature_position)
        self.ui.actionAlignLeft.triggered.connect(lambda: self.feature_align('left'))
        self.ui.actionAlignCentre.triggered.connect(lambda: self.feature_align('centre'))
        self.ui.actionAlignRight.triggered.connect(lambda: self.feature_align('right'))
        self.ui.actionAlignTop.triggered.connect(lambda: self.feature_align('top'))
        self.ui.actionAlignMiddle.triggered.connect(lambda: self.feature_align('middle'))
        self.ui.actionAlignBottom.triggered.connect(lambda: self.feature_align('bottom'))
        
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
        
        # Additional items on toolbar (none standard, so not added through QT designer)
        # Scale selector
        self.ui.toolBar.insertSeparator(self.ui.actionVisit_Website)
        self.scale_label = QLabel("Scale: ")
        self.ui.toolBar.insertWidget(self.ui.actionVisit_Website, self.scale_label)
        self.scale_select_combo = QComboBox()
        self.ui.toolBar.insertWidget(self.ui.actionVisit_Website, self.scale_select_combo)
        #self.ui.toolBar.insertSeparator(self.ui.actionVisit_Website)
        # Populate the Scale pull-down menu
        for scale_text in self.sc.scales.keys():
            self.scale_select_combo.addItem(scale_text)
        self.scale_select_combo.setCurrentText(default_scale)
        self.scale_select_combo.currentIndexChanged.connect(self.scale_change)
        # Wall width selector (in real life actual mm)
        self.wall_width_label = QLabel("Wall width: ")
        self.ui.toolBar.insertWidget(self.ui.actionVisit_Website, self.wall_width_label)
        self.wall_width_combo = QComboBox()
        self.ui.toolBar.insertWidget(self.ui.actionVisit_Website, self.wall_width_combo)
        self.ui.toolBar.insertSeparator(self.ui.actionVisit_Website)
        # Populate the Scale pull-down menu
        for width_option in self.config.wall_width_options:
            self.wall_width_combo.addItem(f"{width_option}mm")
        self.wall_width_combo.setCurrentText(f"{self.config.wall_width}mm")
        self.wall_width_combo.currentIndexChanged.connect(self.width_change)

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
        self.ui.copyWallButton.pressed.connect(self.copy_wall)
        self.ui.editWallButton.pressed.connect(self.edit_wall)
        self.ui.deleteWallButton.pressed.connect(self.delete_wall)
        self.ui.interlockingButton.pressed.connect(self.view_interlocking_window)
        
        # Action buttons when edit wall
        self.ui.closeButton.pressed.connect(self.close_edit)
        self.ui.wallPropertiesButton.pressed.connect(self.wall_properties)
        self.ui.wallTexturesButton.pressed.connect(self.texture_properties)
        self.ui.addFeatureButton.pressed.connect(self.add_feature)
        self.ui.deleteFeatureButton.pressed.connect(self.delete_feature)
        
        # Checkboxes
        self.ui.interlockCheckBox.checkStateChanged.connect(self.read_checkbox)
        self.ui.textureCheckBox.checkStateChanged.connect(self.read_checkbox)
        
        self.set_left_buttons("default")
        
        # Update gconfig based on checkboxes - may need to load these values in future
        # interlocking view option
        self.gconfig.checkbox['il'] = self.ui.interlockCheckBox.isChecked()
        # texture view option
        self.gconfig.checkbox['texture'] = self.ui.textureCheckBox.isChecked()
        
        #self.ui.show()
        self.setCentralWidget(self.ui)
        self.show()
        
    # Align a feature
    # If no feature ignore
    # If only one feature selected apply compared to wall
    # If multiple features then apply to each other - using one that is furthest in that position
    # Or if centre / middle then midpoint between objects
    def feature_align(self, direction, history=True):
        # Check we are in wall edit - don't align otherwise
        # The menu is normally disabled, but check anyway
        if self.current_scene != 'walledit':
            return
        selected_items = self.scenes[self.current_scene].get_selected()
        # If no features selected do nothing
        if (len(selected_items) < 1):
            return
        # If just one then align against wall
        elif (len(selected_items) == 1):
            # selected items is obj view - need it as a feature 
            selected_obj = self.view_scenes[self.current_scene].get_obj_from_obj_view(selected_items[0])
            # old_parameters are what was there before this change (undo)
            old_params = {
                'feature': selected_obj,
                'min_x': selected_obj.min_x,
                'min_y': selected_obj.min_y
                }
            self.view_scenes[self.current_scene].wall.wall_feature_align (direction, selected_obj)
            if history == True:
                # new_parameters is what this change does (redo)
                new_params = {
                    'feature': selected_obj,
                    'min_x': selected_obj.min_x,
                    'min_y': selected_obj.min_y
                    }        
                # Align against wall is the same as a move - so use move as the history 
                self.history.add(f"Align feature {selected_obj.template}", "Move feature", old_params, new_params)
            self.view_scenes[self.current_scene].update(feature_obj_pos=True)
        else:
            # If here then have more than one item
            objs = []
            # need to store all the different values 
            old_params = {
                'features': [],
                'min_x': [],
                'min_y': []
                }
            # New params - save the features and the direction so we can repeat 
            new_params = {
                'features': [],
                'direction': direction
                }
            for item in selected_items:
                obj = self.view_scenes[self.current_scene].get_obj_from_obj_view(item)
                old_params['features'].append(obj)
                new_params['features'].append(obj)
                old_params['min_x'].append(obj.min_x)
                old_params['min_y'].append(obj.min_y)
                objs.append(obj)
            self.view_scenes[self.current_scene].wall.features_align (direction, objs)
            self.view_scenes[self.current_scene].update(feature_obj_pos=True)
            self.history.add(f"Align features", "Align features", old_params, new_params)
            
            
    # Undo feature align - only used when multiple objects moved
    def feature_align_undo (self, old_params, history=False):
        for i in range (0, len(old_params['features'])):
            old_params['features'][i].min_x = old_params['min_x'][i]
            old_params['features'][i].min_y = old_params['min_y'][i]
            old_params['features'][i].update_pos()
        self.view_scenes[self.current_scene].update(feature_obj_pos=True)
            
    # Launch feature position window
    def feature_position (self):
        # This will only be called from wall edit (menu hidden on other screens)
        # But check just in case
        if self.current_scene != "walledit":
            return
        # First need to know feature to use
        # Currently only allows a single feature to be selected and it is positioned relative to the wall
        selected_items = self.scenes[self.current_scene].get_selected()
        # If none or more than one selected then just ignore (at the moment)
        if len(selected_items)!= 1:
            return
        feature = self.view_scenes[self.current_scene].get_obj_from_obj_view(selected_items[0])
        # If first run create window - else use edit_position to reopen window
        if self.feature_pos_window == None:
            self.feature_pos_window = FeaturePosWindowUI(self, self.config, self.gconfig, self.builder)
        self.feature_pos_window.edit_position(self.view_scenes[self.current_scene].wall, feature)
        
    def feature_position_update (self):
        self.view_scenes[self.current_scene].update(feature_obj_pos=True)

    # Scale is stored in self.sc (also in Laser.sc)
    # Scale combo changed
    def scale_change (self):
        new_scale = self.scale_select_combo.currentText()
        self.set_scale(new_scale)
    
    # Set the scale and set the combo box
    def set_scale (self, scale):
        self.sc.set_scale(scale)
        # Also update this menu
        self.scale_select_combo.setCurrentText(scale)
        # Also update the width - note that this will also perform
        # an update with progress bar
        self.width_change()
        
        
    def get_scale (self):
        return self.sc.scale
    
    # Wall width (Wood Width) is kept in config - even when changed
    # Wall width changes - also update using progress bar
    def width_change (self):
        wall_width_string = self.wall_width_combo.currentText()
        # Strip off the mm
        wall_width_string = wall_width_string.rstrip('mm')
        try:
            self.config.wall_width = int(wall_width_string)
        except:
            print ("Warning invalid wall width")
            return
        # Update in the Interlocking class
        material_thickness = self.config.wall_width
        self.scale_material = self.sc.reverse_scale_convert(material_thickness)
        # Set material thickness for Interlocking (class variable)
        Interlocking.material_thickness = self.scale_material
        self.full_update()
        
      
        
    #If item is double clicked then it gets passed to this
    def double_click (self):
        #object = self.view_scenes[self.current_scene].get_obj_from_obj_view(this_obj)
        # If we are in wall edit then edit properties
        if self.current_scene == "walledit":
            self.wall_properties()
        # If not then change to edit wall
        else:
            self.edit_wall()
        
   
    # Check for items in current scene have moved - do we need to update current screen
    def check_obj_moved (self):
        moved = False
        for obj in self.view_scenes[self.current_scene].obj_views:
            if obj.has_moved():
                moved = True
        return moved
        
    # Launch wall properties (edit) window
    def wall_properties(self):
        if self.wall_window == None:
            self.wall_window = WallWindowUI(self, self.config, self.gconfig, self.builder)
        self.wall_window.edit_properties(self.view_scenes[self.current_scene].wall)
        
    # Launch interlocking (view) window
    def view_interlocking_window(self):
        if self.interlocking_window == None:
            self.interlocking_window = InterlockingWindowUI(self, self.config, self.gconfig, self.builder)
        self.interlocking_window.update()
        self.interlocking_window.display()
        
    # Launch texture properties (edit) window
    # Same for add texture and edit texture
    def texture_properties(self):
        if self.texture_window == None:
            self.texture_window = TextureWindowUI(self, self.config, self.gconfig, self.builder)
        self.texture_window.edit_properties(self.view_scenes[self.current_scene].wall)


    def copy_wall(self):
        # Current selected objects (note these are groups containing walls and features / textures etc.)
        # Should  be one selected (otherwise the button should be disabled - but check)
        selected_items = self.scenes[self.current_scene].get_selected()
        # If no items selected then just return
        if selected_items == None:
            return
        else:
            # Now get the selected objs from the selected items (ie. get the wall from the view)
            selected_objs = []
            # Call get info to find information on what is selected
            for this_obj in selected_items:
                selected_objs.append(self.view_scenes[self.current_scene].get_obj_from_obj_view(this_obj))
            # Should only be one selected (don't support copying multiple walls together)
            if len(selected_objs) == 1:
                #print ("Copy selected")
                #print (f"Name: {selected_objs[0].name}")
                #print (f"Type: {selected_objs[0].type}") 
                # Copy in builder
                new_wall = self.builder.copy_wall(selected_objs[0])
                # History moved to builder class
                #old_param = {'wall_copied' : selected_objs[0]}
                #new_param = {'wall_copy': new_wall}
                #self.history.add("Wall copied", "MainWindows copy wall", old_param, new_param) 
                # Update the scene
                self.update_view(self.current_scene)                
        return

    def edit_wall(self):
        selected_items = self.scenes[self.current_scene].get_selected()
        # If no items selected then just return
        if selected_items == None:
            return
        else:
            # Now get the selected objs from the selected items (ie. get the wall from the view)
            selected_objs = []
            # Call get info to find information on what is selected
            for this_obj in selected_items:
                selected_objs.append(self.view_scenes[self.current_scene].get_obj_from_obj_view(this_obj))
            # Should only be one selected (don't support editing multiple walls together)
            if len(selected_objs) != 1:
                return
        # Now have a single object selected (wall)
        self.current_scene = 'walledit'
        self.view_scenes[self.current_scene].edit_wall(selected_objs[0])
        self.change_scene(self.current_scene)
        
    def delete_wall(self):
        selected_items = self.scenes[self.current_scene].get_selected()
        # If no items selected then just return
        if selected_items == None:
            return
        else:
            # Now get the selected objs from the selected items (ie. get the wall from the view)
            selected_objs = []
            # Call get info to find information on what is selected
            for this_obj in selected_items:
                selected_objs.append(self.view_scenes[self.current_scene].get_obj_from_obj_view(this_obj))
            # Should only be one selected (don't support editing multiple walls together)
            if len(selected_objs) != 1:
                return
        # Now have a single object selected (wall)
        #selected_objs[0]
        confirm_box = QMessageBox.question(self, "Are you sure?", f"Are you sure you want\nto delete the selected wall?\n{selected_objs[0].name}")
        if confirm_box == QMessageBox.Yes:
            #old_params = {'old_wall': selected_objs[0]}
            #new_params = {}
            #self.history.add("Delete wall", "MW Wall del", old_params, new_params)
            #print ("Yes delete wall")
            self.builder.delete_wall(selected_objs[0])
            self.update_current_scene()
            # Force refresh of all walls to update any interlocking that has been removed
            self.update_all_views()
        else:
            #print ("No do not delete")
            return

    # Set which of the left menu buttons are hidden / disabled
    # status = default (top level - add button (enabled) / copy button (disabled) / edit wall (disabled)
    # status = wallselect when single wall selected (top level - copy button active and edit wall active)
    # status = walledit - when edit wall option / walleditfeature if a feature is selected in wall edit
    def set_left_buttons(self, status):
        if status == "default" or status == "wallselect":
            self.ui.addWallButton.show()
            #self.ui.addWallButton.setEnabled(True)
            self.ui.copyWallButton.show()
            self.ui.editWallButton.show()
            self.ui.deleteWallButton.show()
            self.ui.interlockingButton.show()
            self.ui.closeButton.hide()
            self.ui.wallPropertiesButton.hide()
            self.ui.wallTexturesButton.hide()
            self.ui.addFeatureButton.hide()
            self.ui.deleteFeatureButton.hide()
            self.ui.actionWallTexture.setVisible(False)
            if status == "wallselect":
                self.ui.copyWallButton.setEnabled(True)
                self.ui.editWallButton.setEnabled(True)
                self.ui.deleteWallButton.setEnabled(True)
            else:
                self.ui.copyWallButton.setEnabled(False)
                self.ui.editWallButton.setEnabled(False)
                self.ui.deleteWallButton.setEnabled(False)
            # Also hide features from menubar
            self.ui.menuFeatures.menuAction().setVisible(False)
        elif status.startswith("walledit"):
            self.ui.addWallButton.hide()
            self.ui.copyWallButton.hide()
            self.ui.editWallButton.hide()
            self.ui.deleteWallButton.hide()
            self.ui.interlockingButton.hide()
            self.ui.closeButton.show()
            self.ui.wallPropertiesButton.show()
            self.ui.wallTexturesButton.show()
            self.ui.addFeatureButton.show()
            self.ui.deleteFeatureButton.show()
            # If in walledit and a feature is selected
            if status == "walleditfeature":
                self.ui.deleteFeatureButton.setEnabled(True)
            else:
                self.ui.deleteFeatureButton.setEnabled(False)
            self.ui.menuFeatures.menuAction().setVisible(True)
            self.ui.actionWallTexture.setVisible(True)
    
    
    def file_new(self):
        if self.history.file_changed == True:
            # Confirm with user 
            confirm_box = QMessageBox.question(self, "File changed", f"Changes to existing file\nOpen file anyway?")
            if confirm_box != QMessageBox.Yes:
                return
        # todo add here
        # Reset values
        self.filename = ""
        self.history = History(self)
        self.current_scene = 'front'
        
        self.builder = Builder(self.config, self.threadpool, self)
        
        self.scenes = {}
        self.view_scenes = {}
        for scene_name in self.config.allowed_views:
            #self.scenes[scene_name] = QGraphicsScene()
            self.scenes[scene_name] = ViewGraphicsScene(self)
            self.view_scenes[scene_name] = ViewScene(self, self.scenes[scene_name], self.builder, self.gconfig, scene_name)
            # Signal for change in viewgraphicsscene (item selected / deselected)
            self.scenes[scene_name].focus_changed.connect(self.update_selected_view)

        # One more scene which is called "walledit" which is used to edit a particular wall
        self.scenes["walledit"] = ViewGraphicsScene(self)
        self.view_scenes['walledit'] = EditScene(self, self.scenes["walledit"], self.builder, self.gconfig, "walledit")
        self.scenes["walledit"].focus_changed.connect(self.update_selected_view)
        
        # Default to front view
        self.ui.graphicsView.setScene(self.scenes[self.current_scene])



    def open_file_dialog(self):
        if self.history.file_changed == True:
            # Confirm with user 
            confirm_box = QMessageBox.question(self, "File changed", f"Changes to existing file\nOpen file anyway?")
            if confirm_box != QMessageBox.Yes:
                return
        
        filename = QFileDialog.getOpenFileName(self, "Open building file", "", "Building file (*.json);;All (*.*)")
        # possibly check for valid file
        if filename[0] == '':
            print ("No filename specified")
            return
        self.ui.statusbar.showMessage ("Loading "+filename[0])
        self.new_filename = filename[0]
        # Create progress window before starting threadpool (needs to be in main thread)
        self.start_progress("Loading ...", 100)
        self.threadpool.start(self.file_open)
        
    # Full update of all files with progress bar
    def full_update(self):
        self.start_progress("Updating ...", 100)
        self.builder.update_walls_td (status_signal=self.builder.wall_update_status_signal, complete_signal=self.builder.wall_update_complete_signal)
        
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
        #print (f"Filename is {filename}")
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
                #print ("Yes replace file")
                pass
            else:
                #print ("No do not replace")
                return
        
        if this_filename == '':
            print ("No filename specified for save")
            return
        self.new_filename = this_filename

        self.ui.statusbar.showMessage ("Saving as "+self.new_filename)
        # Reach here then it's saving in a new file (not overwrite)
        self.threadpool.start(self.file_save)

    # Export file (eg. SVG for laser cutter)
    def export_dialog(self):
        filename = QFileDialog.getSaveFileName(self, "Export building file", "", "SVG file (*.svg);;All (*.*)", "SVG file (*.svg)", QFileDialog.DontConfirmOverwrite)
        #print (f"Filename is {filename}")
        this_filename = filename[0]
        # If no suffix/extension then add here
        # Basic check for extension using os.path.splitext
        file_and_ext = os.path.splitext(this_filename)
        # If there is an extension then just continue (don't check it matches), but if not then add .json
        if (file_and_ext[1] == ""):
            this_filename += ".svg"
        # Check if file exists
        file_info = QFileInfo(this_filename)
        # Due to problem with getSaveFilename and suffix need to create own message box
        # Otherwise whilst the dialog box will check for file replace it will provide filename with suffix added, but only
        # check filename without suffix.
        if file_info.exists():
            # Confirm with user to delete
            confirm_box = QMessageBox.question(self, "File already exists", f"The file:\n{this_filename} already exists.\n\nDo you want to replace this file?")
            if confirm_box == QMessageBox.Yes:
                #print ("Yes replace file")
                pass
            else:
                #print ("No do not replace")
                return
        
        if this_filename == '':
            print ("No filename specified for save")
            return
        self.export_filename = this_filename

        #self.ui.statusbar.showMessage ("Exporting as "+self.export_filename)
        self.start_progress ("Exporting ...", 100)
        # Reach here then it's saving in a new file (not overwrite)
        self.threadpool.start(self.file_export)

    # Performs the actual save (normally triggered in a threadpool)
    def file_save(self):
        print (f"Saving file {self.new_filename}")
        success = self.builder.save_file(self.new_filename)
        # If successful then confirm new filename
        if success[0] == True:
            self.filename = self.new_filename
        # If not then give an error message - need to pass back to GUI thread
        else:
            self.status_message = f"Unable to save {self.new_filename}.\n\nError: {success[1]}"
            self.file_save_warning_signal.emit()
            
    # Performs the actual save (normally triggered in a threadpool)
    def file_export(self):
        #print (f"Exporting file {self.export_filename}")
        success = self.builder.export_file(self.export_filename)
        # If successful then confirm new filename
        # If not then give an error message - need to pass back to GUI thread
        if success[0] != True:
            self.status_message = f"Unable to export {self.new_filename}.\n\nError: {success[1]}"
            self.file_save_warning_signal.emit()
            
    def file_save_warning(self):
        QMessageBox.warning(self, "File save error", self.status_message, QMessageBox.Ok)
        

    def visit_website(self, site=None):
        if site == None:
            webbrowser.open("https://www.penguintutor.com/projects/laser-cut-buildings")

    # File open is called as a separate thread
    def file_open(self):
        # Prevent duplicate file opens (or saving when opening etc.)
        self.disable_file_actions()
        result = self.builder.load_file(self.new_filename)
        if result[0] == False:
            print (f"Error {result[1]}")
            self.ui.statusbar.showMessage ("Error "+result[1])
        else:
            self.filename = self.new_filename
            self.update_status()
        # update load complete message - even if failed as otherwise load is locked
        #self.load_complete_signal.emit()
        
    # Called from load_complete_signal after a file has been loaded
    # Refresh display
    def load_complete(self):
        # Reenable file actions
        self.enable_file_actions()
        self.update_all_views()

    # Whenever performing file action then disable other file actions to prevent duplicates / conflicting
    def disable_file_actions(self):
        self.ui.actionOpen.setEnabled(False)
        
    def enable_file_actions(self):
        self.ui.actionOpen.setEnabled(True)
        
    def update_all_views (self):
        num_views = len(self.config.allowed_views) + 1
        current_view = 0
        for scene_name in self.config.allowed_views:
            self.update_view (scene_name)
        # Also need to check if we are in edit and if so update that
        if self.current_scene == "walledit":
            self.update_view("walledit")
        
    def zoom_out (self):
        # Minimum zoom is 0.125 - actually two values for scale, but just look at x
        #current_scale = self.ui.graphicsView.transform().m11()
        #if current_scale <= 0.125:
        if self.zoom_level <= 0.25:
            return
        else:
            #self.zoom_level -= 0.25
            self.zoom_level = float(self.zoom_level) - 0.25
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
            #self.zoom_level += 0.25
            self.zoom_level = float(self.zoom_level) + 0.25
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

    def update_current_scene (self):
        #print ("Update current scene")
        self.view_scenes[self.current_scene].update()

    def change_scene (self, new_scene):
        # if previous was walledit then need to update
        # the wall
        if self.current_scene == "walledit":
            # perform update of wall on thread then callback to viewscene
            self.view_scenes[self.current_scene].update_switch(self.view_scenes[new_scene])
        # Run an update on the new scene anyway - but texture won't be
        # updated until after the callback from the above update
        self.current_scene = new_scene
        # Does this need an update when changing scene?
        self.view_scenes[new_scene].update()
        self.ui.graphicsView.setScene(self.scenes[self.current_scene])
        self.ui.graphicsView.show()
        # Update table to show nothing selected
        self.update_selected_view(None)
        # Update left menu based on type of scene (eg. direction view / edit wall)
        if new_scene == "walledit":
            self.set_left_buttons("walledit")
        else:
            self.set_left_buttons("default") 
            

    # Add new wall dialog
    def add_wall (self):
        if self.wall_window == None:
            self.wall_window = WallWindowUI(self, self.config, self.gconfig, self.builder)
        self.wall_window.new()

        
    # Check to see if any objects in current scene have moved
    # and if appropriate refresh display
    # Update the selected scene
    def check_moved_update (self):
        if self.check_obj_moved():
            # If it's a wall edit then need to update view
            # But only the 
            if self.current_scene == "walledit":
                #self.view_scenes[self.current_scene].update(full=True)
                #self.view_scenes[self.current_scene].update_full()
                self.view_scenes[self.current_scene].update()       
    
    # Updates table showing status of objects
    # Update based on selection in viewgraphicsscene
    def update_selected_view (self, selected_items):
        # Selection are items selected
        # For normal scenes these are groups (because each wall is composed of groups of items
        # which are in <ObjView>.item_group
        # To know which are selected need to query each of the ObjViews in the current <ViewScene>

        # reset all table rows
        self.ui.infoTable.setRowCount(0)
        
        # Potential race condition - where selected_items is being updated could result in
        # one of the fields being None - so check at each point that have a valid object 

        # First check if some items are selection
        if selected_items != None and len(selected_items)>0 and selected_items[0]!=None:
            selected_objs = []
            # Call get info to find information on what is selected
            for this_obj_view in selected_items:
                this_obj = self.view_scenes[self.current_scene].get_obj_from_obj_view(this_obj_view)
                if this_obj == None:
                    continue
                selected_objs.append(this_obj)
            if (len(selected_objs) > 1):
                self.ui.infoLabel.setText(f"{len(selected_objs)} objects selected")
                self.ui.infoTable.setRowCount(len(selected_objs))
                for i in range (0, len(selected_objs)):
                    self.ui.infoTable.setItem(i,0, QTableWidgetItem(f"Object {i}"))
                    self.ui.infoTable.setItem(i,1, QTableWidgetItem(f"{selected_objs[i].get_summary()}"))
                
                # Disable edit button as more than one selected
                if self.current_scene == "walledit":
                    self.set_left_buttons("walledit")
                else:
                    self.set_left_buttons("default")

            elif (len(selected_objs) == 1):
                self.ui.infoLabel.setText("One object selected")
                info_dict = selected_objs[0].get_summary_dict()
                current_row = 0
                self.ui.infoTable.setRowCount(len(info_dict))
                for this_key in info_dict.keys():
                    self.ui.infoTable.setItem(current_row,0, QTableWidgetItem(this_key))
                    self.ui.infoTable.setItem(current_row,1, QTableWidgetItem(info_dict[this_key]))
                    current_row += 1
                
                if self.current_scene == "walledit":
                    self.set_left_buttons("walleditfeature")
                else:
                    self.set_left_buttons("wallselect")
            else:
                self.ui.infoLabel.setText("No objects selected")
                if self.current_scene == "walledit":
                    self.set_left_buttons("walledit")
                else:
                    self.set_left_buttons("default")
        else:
            self.ui.infoLabel.setText("No objects selected")
            
        
    # Call if checkbox changed
    # Update settings then call appropriate update 
    def read_checkbox (self):
        interlock = self.ui.interlockCheckBox.isChecked()
        self.gconfig.checkbox['il'] = interlock
        texture = self.ui.textureCheckBox.isChecked()
        self.gconfig.checkbox['texture'] = texture
        #self.builder.update_walls(interlock, texture)
        # request update of viewgraphics
        self.update_view(self.current_scene)
        
    # Close the current window (eg edit wall)
    def close_edit (self):
        #self.view_scenes[self.current_scene].wall.update()
        self.view_scenes[self.current_scene].update()
        self.change_scene(self.view_scenes[self.current_scene].get_wall_scene())
        

    # Add feature when in edit wall
    def add_feature (self):
        if self.add_feature_window == None:
            self.add_feature_window = AddFeatureWindowUI(self, self.config, self.gconfig, self.builder, self.view_scenes['walledit'].wall)
        else:
            self.add_feature_window.set_wall(self.view_scenes['walledit'].wall)
            self.add_feature_window.show()

    def delete_feature (self):
        selected_items = self.scenes[self.current_scene].get_selected()
        # First check if some items are selection
        if selected_items != None and len(selected_items) == 1:
            # Get the object to remove from the wall
            obj = self.view_scenes[self.current_scene].get_obj_from_obj_view(selected_items[0])
            # create history    
            new_params = {
                # this is a copy of the entire wall - perhaps just get the id instead
                'feature': copy.copy(obj)
                }
            # Old params are the steps to undo (what the current values are before changing), in this case the feature
            # added so that we can delete it
            old_params = {
                'wall': self.view_scenes["walledit"].wall,
                'feature_type': obj.type,
                'feature_template': obj.template,
                'startpos': [obj.min_x, obj.min_y],
                'points': obj.points,
                'cuts': copy.copy(obj.cuts),
                'etches': copy.copy(obj.etches),
                'outers': copy.copy(obj.outers)
                }
            self.history.add(f"Del feature {obj.template}", "Del feature", old_params, new_params)
            # Delete that obj from the wall
            # Note only works when in walledit - as that is the one that references the wall
            # But the option isn't shown if not in walledit
            self.view_scenes["walledit"].wall.del_feature_obj(obj)
            # delete from the scene
            # not required to specifically remove from view instead just call an update
            self.view_scenes["walledit"].update(selection=False)


    def start_progress (self, status, maximum):
        if (self.progress_window == None):
            self.progress_window = QProgressDialog (status, "Cancel", 0, maximum)
            self.progress_window.setCancelButton(None)
            self.progress_window.setMinimumDuration(500)
            self.progress_window.setWindowModality(Qt.WindowModal)
        else:
            self.progress_window.setLabelText (status)
            self.progress_window.setMaximum (maximum)

    # This is in the main thread
    # If updating from another thread then using emit
    def update_progress_dialog (self, value):
        #print (f"Updating dialog with emit value {value}")
        self.progress_window.setValue(value)
        
    def quit_app(self):
        QCoreApplication.quit()
        
    def closeEvent (self, event):
    # Quit app - check with user first
        if self.history.file_changed == True:
            # Confirm with user 
            confirm_box = QMessageBox.question(self, "Quit without saving", f"Changes have not been saved.\nQuit without saving?")
            if confirm_box == QMessageBox.Yes:
                QCoreApplication.quit()
            else:
                event.ignore()
                return
        # Consider saving geometry
        #settings = QSettings("MyCompany", "MyApp")
        #settings.setValue("geometry", self.saveGeometry())
        #settings.setValue("windowState", self.saveState())
        #QMainWindow.closeEvent(self, event)

    def update_undo_menu(self, action):
        print (f"Updating undo menu {action}")
        self.ui.actionUndo.setEnabled(True)
        self.ui.actionUndo.setText(f"Undo: {action}")
        self.ui.actionRedo.setEnabled(False)
    
    
    def update_redo_menu(self, action):
        self.ui.actionRedo.setEnabled(True)
        self.ui.actionRedo.setText(f"Redo: {action}")
        
    def undo (self):
        self.history.undo()
        # After undo perform an update all
        self.update_all_views()
    
    # Redo not implemented yet
    def redo (self):
        pass
    
    def keyReleaseEvent(self, event):
        if isinstance(event, QKeyEvent):
            key = event.key()
            if key == Qt.Key_Delete:
                if self.current_scene == "walledit":
                    self.delete_feature()
                else:
                    self.delete_wall()
