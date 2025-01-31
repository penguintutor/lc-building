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

app_title = "Add / Edit Wall"

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
        
        # Wall if new then this will be None
        # Otherwise holds the wall that is being edited
        self.wall = None
        
        self.ui = loader.load(os.path.join(basedir, "wallwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
        
        # Set initially to default scale 
        self.sc = Scale("OO")
        
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
        # This has been done manually for each entry as the lambda function doesn't work
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
        # Track changes - can read the value in the method, but need to know which entry updated
        # in case need to update corresponding - eg. if add real size, need to update scale size
        # only need for the first 3 entries as in custom mode then do scale conversion
        # Uses textEdited rather than textChanged - so only triggers when changed by user
        self.ui.wall_input_x_0.textEdited.connect(lambda: self.entry_change('x', 0))
        self.ui.wall_input_x_1.textEdited.connect(lambda: self.entry_change('x', 1))
        self.ui.wall_input_x_2.textEdited.connect(lambda: self.entry_change('x', 2))
        self.ui.wall_input_y_0.textEdited.connect(lambda: self.entry_change('y', 0))
        self.ui.wall_input_y_1.textEdited.connect(lambda: self.entry_change('y', 1))
        self.ui.wall_input_y_2.textEdited.connect(lambda: self.entry_change('y', 2))

            
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
        
        self.ui.scaleCombo.activated.connect(self.scale_update)
        
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
        self.max_rows = 10 # Must not be larger than the number of elements in the UI
        
        # When wall type changed then change UI
        self.ui.wallTypeCombo.activated.connect(self.set_view)

        # Used if need to send a status message (eg. pop-up warning)
        self.status_message = ""
        
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.simple_interface()
        
        #self.ui.show()
        
    # Use when using the window to edit existing wall instead of new
    def edit_properties (self, wall):
        self.wall = wall
        # clear any previous data
        self.reset()
        # set to custom interface
        self.ui.wallTypeCombo.setCurrentIndex(2)
        self.custom_interface()
        # Set values based on wall class
        self.ui.nameText.setText(self.wall.name)
        self.num_rows = len(self.wall.points)
        row = 0
        for point in self.wall.points:
            self.wall_elements["input_x"][row].setText(f"{int(point[0])}")
            self.wall_elements["input_y"][row].setText(f"{int(point[1])}")
            row += 1
            if row > 9:
                break
        # If there are more than 4 points then enable the fields
        for i in range (4, self.num_rows):
            self.show_row(i)
        #todo set profile view
        view = self.wall.view
        #self.ui.profileCombo.currentText().lower()
        index = self.ui.profileCombo.findText(view,  Qt.MatchFixedString)
        self.ui.profileCombo.setCurrentIndex(index)
        self.ui.show()
        
    
    # If a entry changes then do we need to reflect across others
    def entry_change (self, col, row):
        # Only need to update if we are not in custom mode (0 and 1)
        selected = self.ui.wallTypeCombo.currentIndex()
        if selected > 1:
            return
        # Get scale in drop down menu - make sure that scale is set to current factor
        # Should not have changed, but just check
        scale = self.ui.scaleCombo.currentText()
        refresh = False
        if scale != self.sc.scale:
            self.sc.set_scale(scale)
            # if it's not the same then need to update all entries, but continue with this for now
            # as we which is most important (last changed)
            refresh = True
        # if an x value changed then reflect that in the corresponding y (but scaled down)
        if col == 'x':
            current_value = self.wall_elements["input_x"][row].text()
            # check it's a value - using try
            try:
                current_value = float(current_value)
                new_value = int(self.sc.scale_convert(current_value))
                # The text method should not trigger this again (otherwise we end up in a loop)
                self.wall_elements["input_y"][row].setText(f"{new_value}")
            # If it's not a number then ignore (may be change in progress)
            except ValueError:
                pass
        elif col == 'y':
            current_value = self.wall_elements["input_y"][row].text()
            # check it's a value - using try
            try:
                current_value = float(current_value)
                new_value = int(self.sc.reverse_scale_convert(current_value))
                # The text method should not trigger this again (otherwise we end up in a loop)
                self.wall_elements["input_x"][row].setText(f"{new_value}")
            # If it's not a number then ignore (may be change in progress)
            except ValueError:
                pass
        if refresh == True:
            self.scale_update()
    
    # Scale has changed - if showing scale (ie. not custom)
    # then refresh
    def scale_update(self):
        # Only need to update if we are not in custom mode (0 and 1)
        selected = self.ui.wallTypeCombo.currentIndex()
        if selected > 1:
            return
        # Get scale in drop down menu - make sure that scale is set to current factor
        # Should not have changed, but just check
        scale = self.ui.scaleCombo.currentText()
        self.sc.set_scale(scale)
        # Read the first 3 x entries and create scale version in y
        for row in range (0, 4):
            current_value = self.wall_elements["input_x"][row].text()
            # check it's a value - using try
            try:
                current_value = float(current_value)
                new_value = int(self.sc.scale_convert(current_value))
                self.wall_elements["input_y"][row].setText(f"{new_value}")
            # If it's not a number then try going the other way - in case invalid entry in actual
            except ValueError:
                current_value = self.wall_elements["input_y"][row].text()
                # check it's a value - using try
                try:
                    current_value = float(current_value)
                    new_value = int(self.sc.reverse_scale_convert(current_value))
                    self.wall_elements["input_x"][row].setText(f"{new_value}")
                # If it's not a number then ignore already tried the other way
                except ValueError:
                    pass
    
    
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
                    # Warning - if error - note counts from 1
                    # For custom then all values are in mm real size so don't allow fractions
                    # Ie. only if int - could change above to allow float and then round if preferred
                    QMessageBox.warning(self, f"Row {row+1} is invalid", "Row {row+1} not a valid number. Please provide a valid size in mm.")
                    return
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
            
            
        # If wall dimensions changed then also need to update any textures
        self.wall.update_texture_points()
        # Update parent (via main window)
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
        
        

