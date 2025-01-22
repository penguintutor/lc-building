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

    # Dictionary of lists
    # First entry is the title - user friendly string
    # Remaining are tuples with setting name, text to be displayed in the gui
    # followed by default values
    # 0 = "Texture name", 1 = "field 1" etc.
    # field 1 & 2 are both 4 digits, 3 is 2 digit (etch)
    textures = {
        "none": ["None"],
        "brick": [
            "Brick",
            ("brick_height", "Brick height", "65"),
            ("brick_width", "Brick width", "103"),
            ("brick_etch", "Brick etch", "10")
            ],
        "wood": [
            "Wood",
            ("wood_height", "Wood height", "150"),
            ("wood_width", "Wood width", "2000"),
            ("wood_etch", "Wood etch", "10")
            ],
        "tile": [
            "Tile",
            ("tile_height", "Tile height", "120"),
            ("tile_width", "Tile width", "300"),
            ("tile_etch", "Tile etch", "7")
            ]
        }

       
    def __init__(self, parent, config, gconfig, builder):
        super().__init__()
        
        # Connect signal handler
        #self.load_complete_signal.connect(self.load_complete)
        #self.name_warning_signal.connect(self.name_warning)
        self.parent = parent
        
        # Wall if new then this will be None
        # Otherwise holds the wall that is being edited
        self.texture = None
        
        self.ui = loader.load(os.path.join(basedir, "texturewindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
                   
        # Set wall type pull down menu
        for texture_key in self.textures.keys():
            self.ui.textureCombo.addItem(self.textures[texture_key][0])
        
        # Set to 0 - None
        # If already set then need to change
        self.ui.textureCombo.setCurrentIndex(0)
        
        self.ui.textureCombo.activated.connect(self.update_fields)
               
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        # shortcuts to the input fields as list for easy index
        self.labels = [self.ui.texture_label_1, self.ui.texture_label_2, self.ui.texture_label_3]
        self.inputs = [self.ui.texture_input_1, self.ui.texture_input_2, self.ui.texture_input_3]
        self.typicals = [self.ui.typical_label_1, self.ui.typical_label_2, self.ui.typical_label_3]
        
        # Set validator for inputs, only allow digits (typically 4)
        # Mask does not work - instead validate when OK pressed
        #self.ui.texture_input_1.setInputMask("0000")
        #self.ui.texture_input_2.setInputMask("0000")
        #self.ui.texture_input_3.setInputMask("00")
        
        self.texture_select ("none")
        print ("Texture window setup")

    # Give the texture type title (eg. Brick)
    # Returns dictionary key (eg. brick)
    def texture_to_key (self, texture):
        for key in self.textures.keys():
            if self.textures[key][0] == texture:
                return key

    # Return index position in the textures
    # used to get position of the pull-down from the name
    def key_to_index (self, key):
        for i in range (0, len(self.textures)):
            if textures[i] == key:
                return i
        return -1

    # Reset back to default state - called after cancel or OK
    # so next time window opened it's back to defaults
    def reset(self):
        # Set to 0 None
        self.ui.textureCombo.setCurrentIndex(0)
        self.update_fields()
        # Set fields to blank
        self.ui.texture_input_1.setText("")
        self.ui.texture_input_2.setText("")
        self.ui.texture_input_3.setText("")

    
    # Update field names if combo changed
    def update_fields (self):
        # Get the selected entry
        selected = self.ui.textureCombo.currentText()
        # Get the key
        key = self.texture_to_key(selected)
        self.texture_select(key)
    
    # Update fields based on texture
    def texture_select (self, key):
        # get number of fields (excluding title)
        num_fields = len(self.textures[key]) - 1
        for i in range (0, len(self.labels)):
            if i >= num_fields:
                self.labels[i].setText("")
                self.inputs[i].hide()
                self.typicals[i].hide()
            else:
                self.labels[i].setText(self.textures[key][i+1][1])
                self.typicals[i].setText(self.textures[key][i+1][2])
                self.inputs[i].show()
                self.typicals[i].show()
                
    
    #Todo HERE - Continue updating *****
    
    # Use when using the window to edit existing texture instead of new
    # Note that can only edit one texture - but for future support pass textures list
    def edit_properties (self, textures):
        # clear any previous data
        self.reset()
        if textures == None or len(textures)<1:
            print ("No textures")
            self.ui.show()
            return
        # Only edit first texture
        self.texture = textures[0]
        
        menu_pos = self.key_to_index(self.texture.style)
        # This should not be the case but if style is not valid then
        # current texture is corrupt so leave it empty
        if menu_pos < 0:
            return
        
        self.ui.textureCombo.setCurrentIndex(menu_pos)
        self.texture_select(menu_pos)
        
        # Set values based on texture
        num_fields = len(self.textures[self.texture.style]) - 1
        for i in range (1, num_fields):
            this_key = self.textures[self.texture.style][i][0]
            this_value = self.texture.get_setting_str(this_key)
            self.inputs[i].setText(this_value)
        
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
        
        

