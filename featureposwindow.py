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
           
    def __init__(self, parent, config, gconfig, builder):
        super().__init__()
        
        self.parent = parent
        
        self.ui = loader.load(os.path.join(basedir, "featureposwindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
        # Wall and feature are added through edit_position method 
        self.wall = None
        self.feature = None
        

        # Connect buttons to method to update distance calculation
        # Use same for wall and feature and check both for changes
        # Uses clicked instead of toggled, so only triggered once per change
        # otherwise triggered when twice because one is selected and one is deselected
        self.ui.WallTopLeftRadio.clicked.connect(self.radio_updated)
        self.ui.WallTopRadio.clicked.connect(self.radio_updated)
        self.ui.WallTopRightRadio.clicked.connect(self.radio_updated)
        self.ui.WallLeftRadio.clicked.connect(self.radio_updated)
        self.ui.WallCentreRadio.clicked.connect(self.radio_updated)
        self.ui.WallRightRadio.clicked.connect(self.radio_updated)
        self.ui.WallBottomLeftRadio.clicked.connect(self.radio_updated)
        self.ui.WallBottomRadio.clicked.connect(self.radio_updated)
        self.ui.WallBottomRightRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureTopLeftRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureTopRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureTopRightRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureLeftRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureCentreRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureRightRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureBottomLeftRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureBottomRadio.clicked.connect(self.radio_updated)
        self.ui.FeatureBottomRightRadio.clicked.connect(self.radio_updated)
        

        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.ui.show()
    
    
    #def set_wall (self, wall):
    #    self.wall = wall
     
    def edit_position (self, wall, feature):
        # Currently only support relative to wall - so just need wall and feature
        # perhaps allow position relative to other features in future?
        self.wall = wall
        self.feature = feature
        
        self.radio_updated()
        
        self.ui.show()

    # Call if an of the radio buttons changed
    # Also used initially for setup of edit position
    def radio_updated (self):
        # Get coords for wall position
        # default to centre and change if another is selected
        wall_pos = [self.wall.get_maxwidth()/2, self.wall.get_maxheight()/2]
        if self.ui.WallTopLeftRadio.isChecked():
            wall_pos = [0,0]
        elif self.ui.WallTopRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth()/2, 0]
        elif self.ui.WallTopRightRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth(), 0]
        elif self.ui.WallLeftRadio.isChecked():
            wall_pos = [0, self.wall.get_maxheight()/2]
        elif self.ui.WallRightRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth(), self.wall.get_maxheight()/2]
        elif self.ui.WallBottomLeftRadio.isChecked():
            wall_pos = [0, self.wall.get_maxheight()]
        elif self.ui.WallBottomRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth()/2, self.wall.get_maxheight()]
        elif self.ui.WallBottomRightRadio.isChecked():
            wall_pos = [self.wall.get_maxwidth(), self.wall.get_maxheight()]
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
        

        

