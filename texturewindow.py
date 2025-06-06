# Window to add / update texture to a wall

import os
from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtUiTools import QUiLoader
from lcconfig import LCConfig
from gconfig import GConfig
import copy

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
    # These are currently fixed maximum - but if need texture with additional then it will
    # need an update to the ui as well as search for "len(self.labels)"
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
        self.gui = parent  # same as self.parent but helps keep consistancy for history
        
        # Wall should be set when choosing edit properties (launching this window)
        self.wall = None
        # Texture may be None if no textures
        # Otherwise holds the wall that is being edited
        self.texture = None
        
        self.ui = loader.load(os.path.join(basedir, "texturewindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
                   
        # Set wall type pull down menu
        for texture_key in self.textures.keys():
            this_texture = self.textures[texture_key][0]
            self.ui.textureCombo.addItem(this_texture)
        
        # Set to 0 - None
        # If already set then need to change
        self.ui.textureCombo.setCurrentIndex(0)
        
        self.ui.textureCombo.activated.connect(self.update_fields)
               
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        # shortcuts to the input fields as list for easy index
        # currently fixed number of fields - if change that then find
        # anywhere that looks for len(self.labels)
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
        return None

    # Return index position in the textures
    # used to get position of the pull-down from the name
    def key_to_index (self, key):
        i = 0
        for this_key in self.textures.keys():
            if this_key == key:
                return i
            i += 1
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
    
    # Use when using the window to edit existing texture instead of new
    # Note that can only edit one texture - but for future support pass textures list
    def edit_properties (self, wall):
        self.wall = wall
        # clear any previous data
        self.reset()
        if wall.textures == None or len(wall.textures)<1:
            self.texture = None
            #print ("No textures") 
            self.ui.show()
            return
        # Only edit first texture
        self.texture = wall.textures[0]
        
        menu_pos = self.key_to_index(self.texture.style)
        # This should not be the case but if style is not valid then
        # current texture is corrupt so leave it empty
        if menu_pos < 0:
            return
        
        self.ui.textureCombo.setCurrentIndex(menu_pos)
        self.texture_select(self.texture.style)
        
        # Set values based on texture
        num_fields = len(self.textures[self.texture.style])-1
        for i in range (0, num_fields):
            this_key = self.textures[self.texture.style][i+1][0]
            this_value = self.texture.get_setting_str(this_key)
            self.inputs[i].setText(str(this_value))
        
        self.ui.show()
        
    
    # Show entire window - for add new window
    def new(self):
        self.textures = None
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
    # If we don't have an existing texture then this is new
    # Otherwise we need to update the existing texture
    def accept(self):
        #print (f"Wall is {id(self.wall)}")
        # Validate data 
        # Add to builder, then reset and hide window
        # Validates entries
        style = self.texture_to_key(self.ui.textureCombo.currentText())
        
        # Iterate over the fields in the style
        style_settings = {}
        num_fields = len(self.textures[style]) - 1
        for i in range (0, len(self.labels)):
            if i >= num_fields:
                break
            # temp variable to shorten and simplify the code as used multiple times
            # [i+1] skips the first entry which is title of the texture style
            this_texture_setting = self.textures[style][i+1]
            text_value = self.inputs[i].text()
            # First check for an empty string - which is treated as 0,
            # Otherwise needs to be a number
            if text_value == "":
                num_value = 0
            else:
                try:
                    num_value = int(text_value)
                except ValueError:
                    QMessageBox.warning(self, f"{this_texture_setting[1]} is not a valid number", f"{this_texture_setting[1]} is not a valid number. Please provide a valid size in mm.")
                    return
            # Simple check to test for a valid number - only a very basic check that don't end up with less than 0 or a ridiculously large number
            # 0 would count as default if appropriate
            if num_value < 0 or num_value > 100000:
                # Message is slightly different from if not a number
                QMessageBox.warning(self, f"{this_texture_setting[1]} value is not valid", f"{this_texture_setting[1]} value is not valid. Please provide a valid size in mm.")
                return
            style_settings[this_texture_setting[0]] = num_value
            
            
        new_params = {"wall": self.wall, "fullwall": True, "points": [], "style": style, "settings": copy.copy(style_settings)}
        # If existing texture then update
        if self.texture != None:
            # Store old settings for history
            old_params = {"wall": self.wall, "fullwall": self.texture.fullwall, "points": self.texture.points, "style": self.texture.style, "settings": copy.copy(self.texture.settings)}
            self.texture.change_texture(style, style_settings)
            new_params['texture'] = self.texture
            self.gui.history.add (f"Change texture for {self.wall.name}", "Change texture", old_params, new_params)
        else:
            # otherwise this is a new texture
            old_params = None
            # Create new (note [] denotes full wall - which is only option at the moment
            this_texture = self.wall.add_texture(style, [], style_settings)
            new_params['texture'] = this_texture
            self.gui.history.add (f"Add texture for {self.wall.name}", "Change texture", old_params, new_params)
            
        # Note need to update edit view as well
        self.wall.update_etches()
        # Update parent
        self.parent.update_all_views()
        
        # Reset the window and hide
        self.reset()
        self.hide()

