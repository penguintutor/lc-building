# Window to add / update wall or roof
# Currently allows creation using different types (eg. rectangle / apex)
# However all are stored and edited as custom
# May change in future, but will need a change in file format as well as how wall.py
# interprets the different types

import os
from PySide6.QtCore import QCoreApplication, QThreadPool, Signal, QFileInfo, QObject, Qt
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QWidget
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtUiTools import QUiLoader
from scale import Scale
from builder import Builder
from viewscene import ViewScene
from lcconfig import LCConfig
from gconfig import GConfig
from vgraphicsscene import ViewGraphicsScene
from wall import Wall
import copy
import webbrowser
import resources

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Wall texture"

class TextureWindowUI(QMainWindow):
    
    #load_complete_signal = Signal()
    #name_warning_signal = Signal()
       
    def __init__(self, parent, config, gconfig, builder):
    #def __init__(self):
        super().__init__()
        
        # Connect signal handler
        #self.load_complete_signal.connect(self.load_complete)
        #self.name_warning_signal.connect(self.name_warning)
        self.parent = parent
        
        # Wall if new then this will be None
        # Otherwise holds the wall that is being edited
        self.wall = None
        
        self.ui = loader.load(os.path.join(basedir, "texturewindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
                   
        # Set wall type pull down menu
        self.ui.textureCombo.addItem("None")
        self.ui.textureCombo.addItem("Brick")
        self.ui.textureCombo.addItem("Wood")
        
        # Set to 0 - None
        # If already set then need to change
        self.ui.textureCombo.setCurrentIndex(1)
        
        self.ui.textureCombo.activated.connect(self.update_fields)
               
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        
        # Set validator for inputs, only allow digits (typically 4)
        texture_input_1.setInputMask("0000")
        texture_input_2.setInputMask("0000")
        texture_input_3.setInputMask("00")
        
        self.texture_select ("None")
        
    # Update field names if combo changed
    def update_fields (self):
        # Get the selected entry
        selected = self.ui.textureCombo.currentText()
        self.texture_select(selected)
    
    # Update fields based on texture
    def texture_select (self, texture):
        # If none then hide other fields
        if texture == "None":
            texture_label_1.setText("")
            texture_label_2.setText("")
            texture_label_3.setText("")
            texture_input_1.hide()
            texture_input_2.hide()
            texture_input_3.hide()
            typical_label_1.hide()
            typical_label_2.hide()
            typical_label_3.hide()
        # If not none then unhide any hidden labels
        else:
            texture_input_1.show()
            texture_input_2.show()
            texture_input_3.show()
            typical_label_1.show()
            typical_label_2.show()
            typical_label_3.show()
            # Set label text accordingly
            if texture == "Brick":
                texture_input_1.setText("Brick height")
                texture_input_1.setText("Brick width")
                texture_input_1.setText("Brick etch")
                typical_label_1.setText("215mm")
                typical_label_2.setText("65mm")
                typical_label_3.setText("10")
            elif texture == "Wood":
                texture_input_1.setText("Wood height")
                texture_input_1.setText("Wood width")
                texture_input_1.setText("Brick etch")
                typical_label_1.setText("2000mm")
                typical_label_2.setText("150mm")
                typical_label_3.setText("10")
                
    
    #Todo HERE - Continue updating *****
    
    # Use when using the window to edit existing wall instead of new
    def edit_properties (self, texture):
        return
        self.wall = wall
        # clear any previous data
        self.reset()
        # set to custom interface
        self.ui.wallTypeCombo.setCurrentIndex(2)
        self.custom_interface()
        # Set values based on wall class
        self.ui.nameText.setText(self.wall.name)
        row = 0
        for point in self.wall.points:
            self.wall_elements["input_x"][row].setText(f"{point[0]}")
            self.wall_elements["input_y"][row].setText(f"{point[1]}")
            row += 1
            if row > 9:
                break
        # If there are more than 4 points then enable the fields
        for i in range (4, len(self.wall.points)-1):
            self.show_row(i)
        #todo set profile view
        view = self.wall.view
        #self.ui.profileCombo.currentText().lower()
        index = self.ui.profileCombo.findText(view,  Qt.MatchFixedString)
        self.ui.profileCombo.setCurrentIndex(index)
        self.ui.show()
        
    
    # Show entire window - for add new window
    def new(self):
        self.wall = None
        self.ui.show()
        self.ui.activateWindow()
        self.ui.raise_()
        
    # hide entire windows
    def hide(self):
        self.ui.hide()
        
    # Cancel button is pressed
    def cancel(self):
        self.reset()
        self.hide()
    
    # Reset back to default state - called after cancel or OK
    # so next time window opened it's back to defaults
    def reset(self):
        # Set to 0 (rectangle)
        self.ui.wallTypeCombo.setCurrentIndex(0)
        # Set title to blank
        self.ui.nameText.setText("")
        # Set all values to mm and got to rectangle
        for row in range (0, self.max_rows):
            self.wall_elements["input_x"][row].setText("mm")
            self.wall_elements["input_y"][row].setText("mm")
        self.simple_interface()
        
    # Accept button is pressed
    # Todo - allow update as well as new
    def accept(self):
        # Validate data - doesn't matter if some fields are not filled in, but need at least 3 points (triangular wall)
        # Add to builder, then reset and hide window
        # Validates entries
        wall_data = {
            'name' : self.ui.nameText.text(),
            'view' : self.ui.profileCombo.currentText().lower(),
            'points' : []
            }
        # Check for points first as that is a critical error, whereas name would be just a warning
        # If simplified interface then try that first
        # Work through the points provided and add as appropriate
        # Rectangle wall (combo = 0)
        if self.ui.wallTypeCombo.currentIndex() == 0:
            # check we have each of the values
            # width is row 0 - use non scale size
            width = self.wall_elements["input_x"][0].text()
            # check it's an integer string and if so convert to int
            try:
                width = int(width)
            except ValueError:
                QMessageBox.warning(self, "Width not a number", "Width is not a number. Please provide a valid size in mm.")
                return
            # Also check it's not a negative number, or ridiculously large (over 100m)
            if width <= 0 or width > 10000:
                QMessageBox.warning(self, "Width is invalid", "Width is not a valid number. Please provide a valid size in mm.")
                return
            
            # Do the same with height - row 1
            height = self.wall_elements["input_x"][1].text()
            # check it's an integer string and if so convert to int
            try:
                height = int(height)
            except ValueError:
                QMessageBox.warning(self, "Height not a number", "Height is not a number. Please provide a valid size in mm.")
                return
            # Also check it's not a negative number, or ridiculously large (over 100m)
            if height <= 0 or height > 10000:
                QMessageBox.warning(self, "Height is invalid", "Height is not a valid number. Please provide a valid size in mm.")
                return
            # Have width and height so convert into points
            wall_data['points'] = [
                (0,0), (width, 0), 
                (width, height), (0, height),
                (0,0)
                ]
        # Apex wall (type = 1)
        elif self.ui.wallTypeCombo.currentIndex() == 1:
            # check we have each of the values
            # width is row 0 - use non scale size
            width = self.wall_elements["input_x"][0].text()
            # check it's an integer string and if so convert to int
            try:
                width = int(width)
            except ValueError:
                QMessageBox.warning(self, "Width not a number", "Width is not a number. Please provide a valid size in mm.")
                return
            # Also check it's not a negative number, or ridiculously large (over 100m)
            if width <= 0 or width > 10000:
                QMessageBox.warning(self, "Width is invalid", "Width is not a valid number. Please provide a valid size in mm.")
                return
            
            # Do the same with height maximum - row 1
            height_max = self.wall_elements["input_x"][1].text()
            # check it's an integer string and if so convert to int
            try:
                height_max = int(height_max)
            except ValueError:
                QMessageBox.warning(self, "Maximum height not a number", "Maximum height is not a number. Please provide a valid size in mm.")
                return
            # Also check it's not a negative number, or ridiculously large (over 100m)
            if height_max <= 0 or height_max > 10000:
                QMessageBox.warning(self, "Maximum height is invalid", "Maximum height is not a valid number. Please provide a valid size in mm.")
                return
            # and for height minimum - row 2
            height_min = self.wall_elements["input_x"][2].text()
            # check it's an integer string and if so convert to int
            try:
                height_min = int(height_min)
            except ValueError:
                QMessageBox.warning(self, "Minimum height not a number", "Minimum height is not a number. Please provide a valid size in mm.")
                return
            # Also check it's not a negative number, or ridiculously large (over 100m)
            if height_min <= 0 or height_min > 10000:
                QMessageBox.warning(self, "Minimum height is invalid", "Minimum height is not a valid number. Please provide a valid size in mm.")
                return
            # Could check that min is less than max, but if not then get an inverted apex (strange, but let user do if they want)
            #height delta just reduces amount of calculates in generating point and makes it easier to follow
            height_delta = height_max - height_min
            # Create an apex wall
            wall_data['points'] = [
                (0,height_delta), (int(width/2), 0), (width, height_delta), 
                (width, height_max), (0, height_max),
                (0,height_delta)
                ]
        # If it's not one of the simplified ones then it's custom
        # Read in any values that are displayed, ignore any that are not ints and see if we have enough at the end (at least 3)
        # Both x and y must be numbers for it to be considered valid
        else:
            for row in range (0, self.num_rows):
                this_x = self.wall_elements["input_x"][row].text()
                this_y = self.wall_elements["input_y"][row].text()
                # convert to int - if either fail then ignore
                try:
                    this_x = int(this_x)
                    this_y = int(this_y)
                except ValueError:
                    continue
                else:
                    wall_data['points'].append([this_x, this_y])
            # Do we have at least 3?
            if len(wall_data['points']) < 3:
                QMessageBox.warning(self, "Insufficient points", "Insufficient points entered. Please ensure both x and y are valid sizes in mm.")
                return
            # Check if start and last points are equal, if not then complete the rectangle
            if wall_data['points'][0] != wall_data['points'][len(wall_data['points'])-1]:
                wall_data['points'].append(wall_data['points'][0])
             
        # Followin gives a warning but allows proceed with creating
        if (wall_data['name'] == ""):
            return_val = QMessageBox.warning(self, 'Warning name not provided', 'A name was not provided for the wall. Accept default named \"Unknown\"?', QMessageBox.Ok | QMessageBox.Cancel)
            if return_val == QMessageBox.Ok:
                wall_data['name'] = "Unknown"
            else:
                return
        
        # if this is a new wall
        if self.wall == None:
            # Add this wall
            self.builder.add_wall(wall_data)
        # If this is existing wall then update it
        else:
            self.wall.name = wall_data['name']
            # create copy of the list - rather than pass the list which will be edited in future
            self.wall.points = copy.deepcopy(wall_data['points'])
            self.wall.view = wall_data['view']
            
        # Update parent
        self.parent.update_all_views()
        
        # Reset the window and hide
        self.reset()
        self.hide()
        
    # Used to hide a row when in custom mode
    def hide_row(self, row):
        self.wall_elements["label"][row].setText("")
        self.wall_elements["label_x"][row].hide()
        self.wall_elements["label_y"][row].hide()
        self.wall_elements["label_y"][row].hide()
        self.wall_elements["input_x"][row].hide()
        self.wall_elements["input_y"][row].hide()
        self.wall_elements["delete"][row].hide()
        self.wall_elements["add"][row].hide()
        
    # Used to show a row when in custom mode
    def show_row(self, row):
        self.wall_elements["label"][row].setText(f"Point {row+1}")
        self.wall_elements["label_x"][row].show()
        self.wall_elements["label_y"][row].show()
        self.wall_elements["label_y"][row].show()
        self.wall_elements["input_x"][row].show()
        self.wall_elements["input_y"][row].show()
        self.wall_elements["delete"][row].show()
        # if the last allowed row then don't show the add button
        if row < self.max_rows - 1:
            self.wall_elements["add"][row].show()
        
    def custom_interface(self):
        # Change information at the top of the screen
        self.ui.dimensionsText1.setText("Enter dimensions in mm full size (1:1).")
        self.ui.dimensionsText2.setText("All points relative to top left position.")
        # Hide scale option
        self.ui.scaleCombo.hide()
        self.ui.scaleLabel.hide()
        # Minimum of 4 entries (assumes back to start for 5)
        for i in range (0, 4):
            # Change text fields for the main entries
            self.wall_elements["label"][i].setText(f"Point {i+1}")
            # Enable the X and Y labels and input fields
            self.wall_elements["label_x"][i].show()
            self.wall_elements["label_y"][i].setText("Y")
            self.wall_elements["label_y"][i].show()
            self.wall_elements["input_x"][i].show()
            self.wall_elements["input_y"][i].show()
            self.wall_elements["delete"][i].show()
            self.wall_elements["add"][i].show()
            

    # Simple interface used for basic rectangular wall (or initial setup for apex)
    def simple_interface(self):
        # Change information at the top of the screen
        self.ui.dimensionsText1.setText("Enter dimensions in mm.")
        self.ui.dimensionsText2.setText("")
        # Show scale pull-down - only used for UI always save using full size dimensions
        self.ui.scaleCombo.show()
        self.ui.scaleLabel.show()
        # Set text on simple labels
        self.ui.wall_label_0.setText("Wall width:")
        self.ui.wall_label_1.setText("Wall height:")
        self.ui.wall_label_y_0.setText("Scale size:")
        self.ui.wall_label_y_1.setText("Scale size:")
        self.ui.wall_label_y_2.setText("Scale size:")
        # Update all fields to remove delete and add buttons
        for i in range (0, self.max_rows):
            self.wall_elements["label_x"][i].hide()
            self.wall_elements["delete"][i].hide()
            self.wall_elements["add"][i].hide()
        # Hide none standard fields
        # Hide labels
        for i in range (2, self.max_rows):
            # Do not hide first label as that would reformat the window
            # Instead set it to ""
            self.wall_elements["label"][i].setText("")
            # Do not hide label_y for first entries as says "Scale"
            self.wall_elements["label_y"][i].hide()
            self.wall_elements["input_x"][i].hide()
            self.wall_elements["input_y"][i].hide()

        
    # Based on simple interface then adds extra field for additional wall height
    def apex_interface(self):
        self.simple_interface()
        # Set text of the wall height 1 to max
        self.ui.wall_label_1.setText("Wall height max:")
        self.ui.wall_label_2.setText("Wall height min:") 
        # Re-enable line 2
        self.ui.wall_label_2.show()
        self.ui.wall_label_y_2.show()
        self.ui.wall_input_x_2.show()
        self.ui.wall_input_y_2.show()
        
        

