# Window to add / update wall or roof
# Currently allows creation using different types (eg. rectangle / apex)
# However all are stored and edited as custom
# May change in future, but will need a change in file format as well as how wall.py
# interprets the different types

import os
from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtUiTools import QUiLoader
from lcconfig import LCConfig
from gconfig import GConfig

loader = QUiLoader()
basedir = os.path.dirname(__file__)

app_title = "Position feature relative to wall"

class FeaturePosWindowUI(QMainWindow):
           
    def __init__(self, parent, config, gconfig, builder, wall):
        super().__init__()
        
        self.parent = parent
        
        self.ui = loader.load(os.path.join(basedir, "featureposwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
        self.wall = wall
        

        # Connect buttons to method to update distance calculation
        # Use same for wall and feature and check both for changes
        self.ui.wallTopLeftRadio.toggled.connect(self.radio_updated)
        self.ui.wallTopRadio.toggled.connect(self.radio_updated)
        self.ui.wallTopRightRadio.toggled.connect(self.radio_updated)
        self.ui.wallLeftRadio.toggled.connect(self.radio_updated)
        self.ui.wallCentreRadio.toggled.connect(self.radio_updated)
        self.ui.wallRightRadio.toggled.connect(self.radio_updated)
        self.ui.wallBottomLeftRadio.toggled.connect(self.radio_updated)
        self.ui.wallBottomRadio.toggled.connect(self.radio_updated)
        self.ui.wallBottomRightRadio.toggled.connect(self.radio_updated)
        self.ui.featureTopLeftRadio.toggled.connect(self.radio_updated)
        self.ui.featureTopRadio.toggled.connect(self.radio_updated)
        self.ui.featureTopRightRadio.toggled.connect(self.radio_updated)
        self.ui.featureLeftRadio.toggled.connect(self.radio_updated)
        self.ui.featureCentreRadio.toggled.connect(self.radio_updated)
        self.ui.featureRightRadio.toggled.connect(self.radio_updated)
        self.ui.featureBottomLeftRadio.toggled.connect(self.radio_updated)
        self.ui.featureBottomRadio.toggled.connect(self.radio_updated)
        self.ui.wallBottomRightRadio.toggled.connect(self.radio_updated)
        

        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.radio_updated()
        
        self.ui.show()
    
    
    def set_wall (self, wall):
        self.wall = wall

    # Call if an of the radio buttons changed
    # Also used initially for setup
    def radio_updated (self):
        # Get coords for wall position
        # default to centre and change if another is selected
        wall_pos = [self.wall.get_maxwidth()/2, self.wall.get_maxheight()/2]
        if self.ui.wallTopLeftRadio.isChecked():
            wall_pos = [0,0]
        elif self.ui.wallTopRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth()/2, 0]
        elif self.ui.wallTopRightRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth(), 0]
        elif self.ui.wallLeftRadio.isChecked():
            wall_pos = [0, wall.get_maxheight()/2]
        elif self.ui.wallRightRadio.isChecked():
            wall_pos = [wall.get_maxwidth(), wall.get_maxheight()/2]
        elif self.ui.wallBottomLeftRadio.isChecked():
            wall_pos = [0, wall.get_maxheight()]
        elif self.ui.wallBottomRadio.isChecked():
            wall_pos = [wall.get_maxwidth()/2, wall.get_maxheight()]
        elif self.ui.wallBottomRightRadio.isChecked():
            wall_pos = [wall.get_maxwidth(), wall.get_maxheight()]
        print (f"Wall position {wall_pos}")
        
        
    # hide entire windows
    def hide(self):
        self.ui.hide()
        
    # Cancel button is pressed
    def cancel(self):
        self.hide()
          
    # Accept button is pressed
    def accept(self):
        
        index_pos = self.ui.listView.currentIndex().row()
            
        # Add this feature
        # (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None):
        self.wall.add_feature_file (self.feature_directory+"/"+self.list_features[index_pos][0])
        
        self.parent.update_current_scene()
        self.hide()
        

        

