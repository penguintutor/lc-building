# Window to add / update texture to a wall

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
from editinterlockingwindow import EditInterlockingWindowUI

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Wall interlocking" 

class InterlockingWindowUI(QMainWindow):

       
    def __init__(self, parent, config, gconfig, builder):
        super().__init__()
        
        self.parent = parent
        
        self.ui = loader.load(os.path.join(basedir, "interlockingwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.edit_window = None
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
               
        # create list from UI elements to allow reference by index
        self.il_elements = {"edge1":[], "edge2":[], "type":[], "delete":[]}
        for i in range (0, 10):
            exec ("self.il_elements[\"edge1\"].append("+f"self.ui.interlock_{i:02}_a_Label"+")")
            exec ("self.il_elements[\"edge2\"].append("+f"self.ui.interlock_{i:02}_b_Label"+")")
            exec ("self.il_elements[\"type\"].append("+f"self.ui.interlock_{i:02}_type_Label"+")")
            exec ("self.il_elements[\"delete\"].append("+f"self.ui.delButton_{i:02}"+")")
            
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.ui.newInterlockButton.pressed.connect(self.new_interlock)
        
        self.update()
        self.ui.show()
        
    def new_interlock(self):
        if self.edit_window == None:
            self.edit_window = EditInterlockingWindowUI(self.parent, self.config, self.gconfig, self.builder)
        else:
            self.edit_window.new()
        
    def clear (self):
        for i in range (0, 10):
            # set each of the values empty
            self.il_elements['edge1'][i].setText("")
            self.il_elements['edge2'][i].setText("")
            self.il_elements['type'][i].setText("")
            self.il_elements['delete'][i].hide()
        
    # Update list of interlocking groups
    def update (self):
        groups = self.builder.interlocking_groups
        
        # Hide all existing
        self.clear()
        
        num_groups = 0
        for group in groups:
            wall1_wall = self.builder.walls[group.primary_wall].name
            #wall1_edge = self.builder.walls[group.primary_wall].il[group.primary_il].edge
            wall1_edge = group.primary_il.edge
            wall1_string = f"Primary: {wall1_wall}, edge {wall1_edge}"
            # Get type from primary
            il_type = group.primary_il.il_type
            
            self.il_elements['edge1'][num_groups].setText(wall1_string)
            wall2_wall = self.builder.walls[group.secondary_wall].name
            wall2_edge = group.secondary_il.edge
            wall2_string = f"Secondary: {wall2_wall}, edge {wall2_edge}"
            self.il_elements['edge2'][num_groups].setText(wall2_string)
            
            self.il_elements['type'][num_groups].setText(il_type)
            self.il_elements['delete'][num_groups].show()
            
            num_groups += 1
            

    def display (self):
        self.ui.show()


    # hide entire windows
    def hide(self):
        self.ui.hide()

    
    # Accept button is pressed
    # If we don't have an existing texture then this is new
    # Otherwise we need to update the existing texture
    def accept(self):
        self.ui.hide()

