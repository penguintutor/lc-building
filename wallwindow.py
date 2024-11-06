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
       
    def __init__(self, config, gconfig, builder):
    #def __init__(self):
        super().__init__()
        
        # Connect signal handler
        #self.load_complete_signal.connect(self.load_complete)
        #self.name_warning_signal.connect(self.name_warning)
        
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
        
        # When wall type changed then change UI
        self.ui.wallTypeCombo.activated.connect(self.set_view)

        # Used if need to send a status message (eg. pop-up warning)
        self.status_message = ""
        
        self.ui.buttonBox.rejected.connect(self.hide)
        
        # temp
        #self.ui.wall_delete_0.pressed.connect(self.view_bottom)
        
        self.simple_interface()
        
        self.ui.show()
    
    # Change these to add / delete entries
    def del_entry(self, entry_num):
        print (f"Del entry {entry_num}")
        
    def add_entry(self, entry_num):
        print (f"Add entry {entry_num}")
    
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
    
    def show(self):
        self.ui.show()
        
    def hide(self):
        self.ui.hide()
        
    def custom_interface(self):
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
        # Set text on simple labels
        self.ui.wall_label_0.setText("Wall width:")
        self.ui.wall_label_1.setText("Wall height:")
        self.ui.wall_label_y_0.setText("Scale size:")
        self.ui.wall_label_y_1.setText("Scale size:")
        self.ui.wall_label_y_2.setText("Scale size:")
        # Update all fields to remove delete and add buttons
        for i in range (0, 10):
            self.wall_elements["label_x"][i].hide()
            self.wall_elements["delete"][i].hide()
            self.wall_elements["add"][i].hide()
        # Hide none standard fields
        # Hide labels
        for i in range (2, 10):
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
        
        

