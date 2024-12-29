# Window to add / update wall or roof
# Currently allows creation using different types (eg. rectangle / apex)
# However all are stored and edited as custom
# May change in future, but will need a change in file format as well as how wall.py
# interprets the different types

import os
from PySide6.QtCore import QCoreApplication, QThreadPool, Signal, QFileInfo, QObject
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QWidget
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtUiTools import QUiLoader
from scale import Scale
from builder import Builder
from viewscene import ViewScene
from lcconfig import LCConfig
from gconfig import GConfig
from vgraphicsscene import ViewGraphicsScene
import webbrowser
import resources

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Add Feature to Wall"

class AddFeatureWindowUI(QMainWindow):
           
    def __init__(self, parent, config, gconfig, builder):
        super().__init__()
        
        self.parent = parent
        self.feature_directory = "features"
        
        self.ui = loader.load(os.path.join(basedir, "addfeaturewindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
        
        # Load features from directory
        self.list_features = self.get_list_features (self.feature_directory)
        # Need to create list as
        # QtCore.QAbstractListModel
        
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.ui.show()
    
    
    def get_list_features (self, directory):
        # currently just get list of files
        # Update to scan contents for titles & types
        file_data = {}
        files = os.listdir(directory) 
        for file in files:
            print (f"File is {file}")
            # Convert into summary indexed by filename
            file_data['file'] = f"This file {file}"
        return file_data
    
    # Del an entry - delete entry, move others up and if > min remove bottom row
    def del_entry(self, entry_num):
        # Are there entries after this in which case move up
        if entry_num < self.num_rows - 1:
            for row in range (entry_num, self.num_rows):
                # If the number of rows is the maximum then we don't have one to copy from so skip
                if row >= self.num_rows -1:
                    continue
                self.wall_elements["input_x"][row].setText(self.wall_elements["input_x"][row+1].text())
                self.wall_elements["input_y"][row].setText(self.wall_elements["input_x"][row+1].text())
        # If there are more than the minimum then hide the last one
        if self.num_rows > self.min_rows:
            self.num_rows -= 1
            self.hide_row(self.num_rows)
        # otherwise set the last row to mm mm
        else:
            self.wall_elements["input_x"][self.num_rows-1].setText("mm")
            self.wall_elements["input_y"][self.num_rows-1].setText("mm")

        
            
    # Add an entry inserting below (ie +1 ) current entry and enabling next display
    # Warning if we have maximum entries then the last one will be lost
    def add_entry(self, entry_num):
        # If not the last entry then shift values down
        if entry_num < self.num_rows - 1:
            for row in range (self.num_rows, entry_num, -1):
                # if last entry then skip, this will lose the last entry but prevent exceeding the list
                if row+1 >= self.max_rows:
                    continue
                self.wall_elements["input_x"][row+1].setText(self.wall_elements["input_x"][row].text())
                self.wall_elements["input_y"][row+1].setText(self.wall_elements["input_x"][row].text())
            # Set current row to mm
            self.wall_elements["input_x"][entry_num+1].setText("mm")
            self.wall_elements["input_y"][entry_num+1].setText("mm")
        #if there are less than the max then add a new entry
        if self.num_rows < self.max_rows:
            self.show_row(self.num_rows)
            self.num_rows += 1
        #print (f"Add entry {entry_num}")
    
    # Change the view based on type combo selection
    def set_view(self):
        selected = self.ui.wallTypeCombo.currentIndex()
        # 0 is rectangle - simplified view
        if selected == 0:
            self.simple_interface()
        # Apex view
        elif selected == 1:
            self.apex_interface()
        else:
            self.custom_interface()
    
    # Show entire window
    def show(self):
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
            if height <= 0 or height > 10000:
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
            if height <= 0 or height > 10000:
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
            
        # Add this wall
        self.builder.add_wall(wall_data)
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
        
    # Used to hide a row when in custom mode
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
        
        

