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
        
        # Default position top left (but normally override before use)
        self.wall_pos = [0,0]
        

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
        # Save self.wall_pos as saves recalculating later - but just use the feature position
        # to populate the ui
        self.wall_pos = [self.wall.get_maxwidth()/2, self.wall.get_maxheight()/2]
        if self.ui.WallTopLeftRadio.isChecked():
            self.wall_pos = [0,0]
        elif self.ui.WallTopRadio.isChecked():
            self.wall_pos = [self.wall.get_maxwidth()/2, 0]
        elif self.ui.WallTopRightRadio.isChecked():
            self.wall_pos = [self.wall.get_maxwidth(), 0]
        elif self.ui.WallLeftRadio.isChecked():
            self.wall_pos = [0, self.wall.get_maxheight()/2]
        elif self.ui.WallRightRadio.isChecked():
            self.wall_pos = [self.wall.get_maxwidth(), self.wall.get_maxheight()/2]
        elif self.ui.WallBottomLeftRadio.isChecked():
            self.wall_pos = [0, self.wall.get_maxheight()]
        elif self.ui.WallBottomRadio.isChecked():
            self.wall_pos = [self.wall.get_maxwidth()/2, self.wall.get_maxheight()]
        elif self.ui.WallBottomRightRadio.isChecked():
            self.wall_pos = [self.wall.get_maxwidth(), self.wall.get_maxheight()]

        feature_pos = [self.feature.min_x + self.feature.get_maxwidth()/2, self.feature.min_y + self.feature.get_maxheight()/2]
        if self.ui.FeatureTopLeftRadio.isChecked():
            feature_pos = [self.feature.min_x, self.feature.min_y]
        elif self.ui.FeatureTopRadio.isChecked():
            feature_pos = [self.feature.min_x + self.feature.get_maxwidth()/2, self.feature.min_y]
        elif self.ui.FeatureTopRightRadio.isChecked():
            feature_pos = [self.feature.min_x + self.feature.get_maxwidth(), self.feature.min_y]
        elif self.ui.FeatureLeftRadio.isChecked():
            feature_pos = [self.feature.min_x + 0, self.feature.min_y + self.feature.get_maxheight()/2]
        elif self.ui.FeatureRightRadio.isChecked():
            feature_pos = [self.feature.min_x + self.feature.get_maxwidth(), self.feature.min_y + self.feature.get_maxheight()/2]
        elif self.ui.FeatureBottomLeftRadio.isChecked():
            feature_pos = [self.feature.min_x, self.feature.min_y + self.feature.get_maxheight()]
        elif self.ui.FeatureBottomRadio.isChecked():
            feature_pos = [self.feature.min_x + self.feature.get_maxwidth()/2, self.feature.min_y + self.feature.get_maxheight()]
        elif self.ui.FeatureBottomRightRadio.isChecked():
            feature_pos = [self.feature.min_x + self.feature.get_maxwidth(), self.feature.min_y + self.feature.get_maxheight()]

        x_dist = feature_pos[0] - self.wall_pos[0] 
        y_dist = feature_pos[1] - self.wall_pos[1] 
        
        self.ui.XDistanceEdit.setText(str(int(x_dist)))
        self.ui.YDistanceEdit.setText(str(int(y_dist)))

        
    # hide entire windows
    def hide(self):
        self.ui.hide()
        
    # Cancel button is pressed
    def cancel(self):
        self.hide()
          
    # Accept button is pressed
    def accept(self):
        
        x_dist_str = self.ui.XDistanceEdit.text()
        # check it's an integer string and if so convert to int
        try:
            x_dist = int(x_dist_str)
        except ValueError:
            QMessageBox.warning(self, "X distance is not a number", "X distance is not a number. Please provide a distance in mm.")
            return
        # Also check it's not a negative number, or ridiculously large (over 100m)
        if x_dist < -10000 or x_dist > 10000:
            QMessageBox.warning(self, "X distance is invalid", "X distance is not a valid number. Please provide a valid size in mm.")
            return
        
        y_dist_str = self.ui.YDistanceEdit.text()
        # check it's an integer string and if so convert to int
        try:
            y_dist = int(y_dist_str)
        except ValueError:
            QMessageBox.warning(self, "Y distance is not a number", "Y distance is not a number. Please provide a distance in mm.")
            return
        # Also check it's not a negative number, or ridiculously large (over 100m)
        if y_dist < -10000 or y_dist > 10000:
            QMessageBox.warning(self, "Y distance is invalid", "Y distance is not a valid number. Please provide a valid size in mm.")
            return
        
        # Update the x_dist / y_dist based on the selected position
        # current value is relative to top left - so default to that
        if self.ui.FeatureTopRadio.isChecked():
            x_dist -= self.feature.get_maxwidth()/2
        elif self.ui.FeatureTopRightRadio.isChecked():
            x_dist -= self.feature.get_maxwidth()
        elif self.ui.FeatureLeftRadio.isChecked():
            y_dist -= self.feature.get_maxheight()/2
        elif self.ui.FeatureCentreRadio.isChecked():
            x_dist -= self.feature.get_maxwidth()/2
            y_dist -= self.feature.get_maxheight()/2
        elif self.ui.FeatureRightRadio.isChecked():
            x_dist -= self.feature.get_maxwidth()
            y_dist -= self.feature.get_maxheight()/2
        elif self.ui.FeatureBottomLeftRadio.isChecked():
            y_dist -= self.feature.get_maxheight()
        elif self.ui.FeatureBottomRadio.isChecked():
            x_dist -= self.feature.get_maxwidth()/2
            y_dist -= self.feature.get_maxheight()
        elif self.ui.FeatureBottomRightRadio.isChecked():
            x_dist -= self.feature.get_maxwidth()
            y_dist -= self.feature.get_maxheight()
        
        # Update the Feature position
        self.feature.min_x = self.wall_pos[0] + x_dist
        self.feature.min_y = self.wall_pos[1] + y_dist

        self.feature.update_pos()
        self.parent.feature_position_update()
        self.ui.hide()
        