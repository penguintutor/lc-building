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

app_title = "Add Wall / Roof"

#class WallWindowUI(QObject):
#class WallWindowUI(QWidget):
class WallWindowUI(QMainWindow):
    
    #load_complete_signal = Signal()
    #name_warning_signal = Signal()
       
    def __init__(self, parent, config, gconfig, builder):
    #def __init__(self):
        super().__init__()
        
        # Connect signal handler
        #self.load_complete_signal.connect(self.load_complete)
        #self.name_warning_signal.connect(self.name_warning)
        self.parent = parent
        
        self.ui = loader.load(os.path.join(basedir, "wallwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
        
        # Generate lists to allow access to the different fields
        # Simplifies translation and iteration over ui elements
        # Dict for each field and list of num 0 to 9
        self.wall_elements = {"label":[], "label_x":[], "label_y":[], "input_x":[], "input_y":[], "delete":[], "add":[]}
        for i in range (0, 10):
            exec ("self.wall_elements[\"label\"].append(self.ui.wall_label_"+str(i)+")")
            exec ("self.wall_elements[\"label_x\"].append(self.ui.wall_label_x_"+str(i)+")")
            exec ("self.wall_elements[\"label_y\"].append(self.ui.wall_label_y_"+str(i)+")")
            exec ("self.wall_elements[\"input_x\"].append(self.ui.wall_input_x_"+str(i)+")")
            exec ("self.wall_elements[\"input_y\"].append(self.ui.wall_input_y_"+str(i)+")")
            exec ("self.wall_elements[\"delete\"].append(self.ui.wall_delete_"+str(i)+")")
            exec ("self.wall_elements[\"add\"].append(self.ui.wall_add_"+str(i)+")")
            
        # Enable click actions on delete and add
        # This has been donemanually for each entry as the lambda function doesn't work
        # inside the exec function
        self.ui.wall_delete_0.pressed.connect(lambda: self.del_entry(0))
        self.ui.wall_delete_1.pressed.connect(lambda: self.del_entry(1))
        self.ui.wall_delete_2.pressed.connect(lambda: self.del_entry(2))
        self.ui.wall_delete_3.pressed.connect(lambda: self.del_entry(3))
        self.ui.wall_delete_4.pressed.connect(lambda: self.del_entry(4))
        self.ui.wall_delete_5.pressed.connect(lambda: self.del_entry(5))
        self.ui.wall_delete_6.pressed.connect(lambda: self.del_entry(6))
        self.ui.wall_delete_7.pressed.connect(lambda: self.del_entry(7))
        self.ui.wall_delete_8.pressed.connect(lambda: self.del_entry(8))
        self.ui.wall_delete_9.pressed.connect(lambda: self.del_entry(9))
        self.ui.wall_add_0.pressed.connect(lambda: self.add_entry(0))
        self.ui.wall_add_1.pressed.connect(lambda: self.add_entry(1))
        self.ui.wall_add_2.pressed.connect(lambda: self.add_entry(2))
        self.ui.wall_add_3.pressed.connect(lambda: self.add_entry(3))
        self.ui.wall_add_4.pressed.connect(lambda: self.add_entry(4))
        self.ui.wall_add_5.pressed.connect(lambda: self.add_entry(5))
        self.ui.wall_add_6.pressed.connect(lambda: self.add_entry(6))
        self.ui.wall_add_7.pressed.connect(lambda: self.add_entry(7))
        self.ui.wall_add_8.pressed.connect(lambda: self.add_entry(8))
        self.ui.wall_add_9.pressed.connect(lambda: self.add_entry(9))
            
        # Set wall type pull down menu
        self.ui.wallTypeCombo.addItem("Rectangular")
        self.ui.wallTypeCombo.addItem("Apex")
        self.ui.wallTypeCombo.addItem("Custom")
        
        # Set Scale pull down menu based on config
        for this_scale in Scale.scales.keys():
            self.ui.scaleCombo.addItem(this_scale)
        # Defaults to position 1 (OO)
        # May want to do this application wide instead of in this menu
        self.ui.scaleCombo.setCurrentIndex(1)
        
        # Profile view combo box default to front 1st entry
        # Need to convert to lower case when saved
        self.ui.profileCombo.addItem("Front")
        self.ui.profileCombo.addItem("Right")
        self.ui.profileCombo.addItem("Rear")
        self.ui.profileCombo.addItem("Left")
        self.ui.profileCombo.addItem("Top")
        self.ui.profileCombo.addItem("Bottom") 
        
        # Number of rows displayed in custom view (minimum is 4)
        self.num_rows = 4
        self.min_rows = 4
        self.max_rows = 10	# Must not be larger than the number of elements in the UI
        
        # When wall type changed then change UI
        self.ui.wallTypeCombo.activated.connect(self.set_view)

        # Used if need to send a status message (eg. pop-up warning)
        self.status_message = ""
        
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.simple_interface()
        
        self.ui.show()
    
    
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
            # Also check it's not a negative number
            if width <= 0:
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
            # Also check it's not a negative number
            if height <= 0:
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
            # Also check it's not a negative number
            if width <= 0:
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
            # Also check it's not a negative number
            if height_max <= 0:
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
            # Also check it's not a negative number
            if height_min <= 0:
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
                this_width = self.wall_elements["input_x"][row].text()
                this_height = self.wall_elements["input_x"][row].text()
                # convert to int - if either fail then ignore
                try:
                    this_width = int(this_width)
                    this_height = int(this_height)
                except ValueError:
                    continue
                else:
                    wall_data['points'].append([this_width, this_height])
            # Do we have at least 3?
            if len(wall_data['points']) < 3:
                QMessageBox.warning(self, "Insufficient points", "Insufficient points entered. Please ensure both x and y are valid sizes in mm.")
                return
            # Check if start and last points are equal, if not then complete the rectangle
            if wall_data['points'][0] != wall_data['points'][len(wall_data['points'])-1]:
                wall_data['points'].append(wall_data['points'][0])
        
        # If it's a custom view
        #### for row in range (entry_num, self.num_rows):
        
        # Warning but proceed with creating
        if (wall_data['name'] == ""):
            wall_data['name'] = "Unknown"
            QMessageBox.warning(self, "Warning name not provided", "A name was not provided for the wall. The wall will be called \"Unknown\"")
            
        # Add this wall
        self.builder.add_wall(wall_data)
        # Update parent
        self.parent.update_all_views()
        
        # Reset the window and hide
        self.reset
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
        
        

