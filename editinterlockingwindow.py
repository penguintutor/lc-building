# Window to add / update interlocking

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
import webbrowser
import resources

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Wall interlocking" 

class EditInterlockingWindowUI(QMainWindow):

       
    def __init__(self, parent, config, gconfig, builder):
        super().__init__()
        
        self.parent = parent
        
        self.ui = loader.load(os.path.join(basedir, "editinterlockingwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.walls = builder.walls
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
            
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.ui.primaryWallCombo.activated.connect(self.update_edge_primary)
        self.ui.secondaryWallCombo.activated.connect(self.update_edge_secondary)
       
        self.update()
        self.ui.show()
        
    def clear (self):
        # Set lists to default position
        self.ui.primaryWallCombo.setCurrentIndex(0)
        self.ui.primaryEdgeCombo.setCurrentIndex(0)
        self.ui.primaryReverseCombo.setCurrentIndex(0)
        self.ui.secondaryWallCombo.setCurrentIndex(0)
        self.ui.secondaryEdgeCombo.setCurrentIndex(0)
        self.ui.secondaryReverseCombo.setCurrentIndex(0)
        
        self.ui.stepEditLine.setText("")
        self.ui.startEditLine.setText("")
        self.ui.endEditLine.setText("")
        
    # Add walls to primary and secondary lists
    # Note that because of dummy first entry - this is offset 1 from the walls list index
    def add_walls (self):
        # First remove all except first entry ("Select ...")
        # primary and secondary are in sync so just use primary
        while self.ui.primaryWallCombo.count() > 1:
            # Make a copy so don't recalculate after removing
            num_items = self.ui.primaryWallCombo.count()
            self.ui.primaryWallCombo.removeItem(num_items-1)
            self.ui.secondaryWallCombo.removeItem(num_items-1)
        # remove edges
        while self.ui.primaryEdgeCombo.count() > 1:
            # Make a copy so don't recalculate after removing
            num_items = self.ui.primaryEdgeCombo.count()
            self.ui.primaryEdgeCombo.removeItem(num_items-1)
            self.ui.secondaryEdgeCombo.removeItem(num_items-1)
            
        # Add walls
        i = 1 # Just used for what we display to the user so start at 1
        for wall in self.walls:
            self.ui.primaryWallCombo.addItem(f"{i}: {wall.name}")
            self.ui.secondaryWallCombo.addItem(f"{i}: {wall.name}")
            i+=1
            
    def update_edge_primary (self):
        self.update_edge_combo("primary")
    
    def update_edge_secondary (self):
        self.update_edge_combo("secondary")
    
    # Update the edge combo based on the wall combo
    # updates can be none (do nothing), "primary", "secondary" or "both"
    # whichever is chosen will result in the edges being removed for that
    def update_edge_combo (self, updates="None"):
        if updates == "primary" or updates == "both":
            # Get wall for primary (-1 to ignore the title menu option)
            primary_wall_id = self.ui.primaryWallCombo.currentIndex() - 1
            # remove all the current edges
            while self.ui.primaryEdgeCombo.count() > 1:
                # Make a copy so don't recalculate after removing
                num_items = self.ui.primaryEdgeCombo.count()
                self.ui.primaryEdgeCombo.removeItem(num_items-1)
            # If wall selected then add edges - add edge number and start / end positions
            # Already taken into consideration 0
            if primary_wall_id >= 0:
                this_wall = self.builder.walls[primary_wall_id]
                edges = this_wall.get_edges_str()
                for this_edge in edges:
                    self.ui.primaryEdgeCombo.addItem(this_edge)
        if updates == "secondary" or updates == "both":
            # Get wall for secondary (-1 to ignore the title menu option)
            secondary_wall_id = self.ui.secondaryWallCombo.currentIndex() - 1
            # remove all the current edges
            while self.ui.secondaryEdgeCombo.count() > 1:
                # Make a copy so don't recalculate after removing
                num_items = self.ui.secondaryEdgeCombo.count()
                self.ui.secondaryEdgeCombo.removeItem(num_items-1)
            # If wall selected then add edges - add edge number and start / end positions
            # Already taken into consideration 0
            if secondary_wall_id >= 0:
                this_wall = self.builder.walls[secondary_wall_id]
                edges = this_wall.get_edges_str()
                for this_edge in edges:
                    self.ui.secondaryEdgeCombo.addItem(this_edge)
                
                
        
        
    def new (self):
        self.ui.show()
        
    # Update list of interlocking groups
    def update (self):
        self.add_walls()
            

    def display (self):
        self.ui.show()


    # hide entire windows
    def hide(self):
        self.ui.hide()

    
    def cancel(self):
        self.clear()
        self.hide()
    
    # Accept button is pressed
    # This is new
    # Todo add ability to edit for future
    def accept(self):
        
        primary_wall_id = self.ui.primaryWallCombo.currentIndex() - 1
        if primary_wall_id < 0:
            QMessageBox.warning(self, f"Select primary wall", f"Primary wall not selected, select a wall from the list.")
            return
        primary_edge_id = self.ui.primaryEdgeCombo.currentIndex() - 1
        if primary_edge_id < 0:
            QMessageBox.warning(self, f"Select primary edge", f"Primary edge not selected, select an edge from the list.")
            return
        primary_reverse = self.ui.primaryReverseCombo.currentIndex()
        
        secondary_wall_id = self.ui.secondaryWallCombo.currentIndex() - 1
        if secondary_wall_id < 0:
            QMessageBox.warning(self, f"Select secondary wall", f"Secondary wall not selected, select a wall from the list.")
            return
        secondary_edge_id = self.ui.secondaryEdgeCombo.currentIndex() - 1
        if secondary_edge_id < 0:
            QMessageBox.warning(self, f"Select secondary edge", f"Secondary edge not selected, select an edge from the list.")
            return
        secondary_reverse = self.ui.secondaryReverseCombo.currentIndex()
        
        step_string = self.ui.stepEditLine.text()
        # Mandatory - must be a number
        try:
            step_value = int(step_string)
        except ValueError:
            QMessageBox.warning(self, f"Step value is not a valid number", f"Step value is not a valid number. Please provide a valid size in mm.")
            return

        # start and end default to 0
        start_string = self.ui.startEditLine.text()
        if start_string == "":
            start_value = 0
        else:
            try:
                start_value = int(start_string)
            except ValueError:
                QMessageBox.warning(self, f"Start is not a valid number", f"Start is not a valid number. Please provide a valid size in mm or leave blank.")
                return

        end_string = self.ui.endEditLine.text()
        if end_string == "":
            end_value = 0
        else:
            try:
                end_value = int(end_string)
            except ValueError:
                QMessageBox.warning(self, f"End is not a valid number", f"End is not a valid number. Please provide a valid size in mm or leave blank")
                return
            
        parameters = {"start" : start_value, "end" : end_value}
 
        # Add this interlocking
        # type is set to default as that is all that is currently supported
        self.builder.add_il(primary_wall_id, primary_edge_id, primary_reverse, secondary_wall_id, secondary_edge_id, secondary_reverse, "default", step_value, parameters)
        
        # Each of the updated walls needs to update their cuts
        self.builder.walls[primary_wall_id].update_cuts()
        self.builder.walls[secondary_wall_id].update_cuts()
        
        self.parent.update()
        self.clear()
        self.ui.hide()

