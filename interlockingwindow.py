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
        
        self.ui.delButton_00.pressed.connect(lambda: self.del_entry(0))
        self.ui.delButton_01.pressed.connect(lambda: self.del_entry(1))
        self.ui.delButton_02.pressed.connect(lambda: self.del_entry(2))
        self.ui.delButton_03.pressed.connect(lambda: self.del_entry(3))
        self.ui.delButton_04.pressed.connect(lambda: self.del_entry(4))
        self.ui.delButton_05.pressed.connect(lambda: self.del_entry(5))
        self.ui.delButton_06.pressed.connect(lambda: self.del_entry(6))
        self.ui.delButton_07.pressed.connect(lambda: self.del_entry(7))
        self.ui.delButton_08.pressed.connect(lambda: self.del_entry(8))
        self.ui.delButton_09.pressed.connect(lambda: self.del_entry(9))
        
        self.update()
        self.ui.show()
        
    def del_entry (self, entry_id):
        # Delete secondary, then primary
        groups = self.builder.interlocking_groups
        wall2 = self.builder.walls[groups[entry_id].secondary_wall]
        il2 = groups[entry_id].secondary_il
        wall2.il.remove(il2)
        wall1 = self.builder.walls[groups[entry_id].primary_wall]
        il1 = groups[entry_id].primary_il
        wall1.il.remove(il1)
        # Remove from group last (otherwise can't get details)
        self.builder.del_il_group(entry_id)


        # Update the current window
        self.update()
        # refresh all windows (as may include walls on different views etc.)
        self.parent.update_all_views()
        

        
    def new_interlock(self):
        if self.edit_window == None:
            self.edit_window = EditInterlockingWindowUI(self, self.config, self.gconfig, self.builder)
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
    # Do we need to update parent - if so set parent to true
    def update (self, parent=False):
        groups = self.builder.interlocking_groups
        #print (f"Num il groups {len(groups)}")
                
        # Hide all existing
        self.clear()
        
        num_groups = 0
        for group in groups:
            wall1_wall = self.builder.walls[group.primary_wall].name
            #wall1_edge = self.builder.walls[group.primary_wall].il[group.primary_il].edge
            # + 1 more user friendly starting at 1 (consistant with edit)
            wall1_edge = group.primary_il.edge +1
            wall1_string = f"Primary: {wall1_wall}, edge {wall1_edge}"
            # Get type from primary
            il_type = group.primary_il.il_type
            
            self.il_elements['edge1'][num_groups].setText(wall1_string)
            wall2_wall = self.builder.walls[group.secondary_wall].name
            wall2_edge = group.secondary_il.edge +1
            wall2_string = f"Secondary: {wall2_wall}, edge {wall2_edge}"
            self.il_elements['edge2'][num_groups].setText(wall2_string)
            
            self.il_elements['type'][num_groups].setText(il_type)
            self.il_elements['delete'][num_groups].show()
            
            num_groups += 1
        if (parent):
            self.parent.update_all_views()
            

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

