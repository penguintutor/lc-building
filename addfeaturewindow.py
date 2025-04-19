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

app_title = "Add Feature to Wall"

class AddFeatureWindowUI(QMainWindow):
           
    def __init__(self, parent, config, gconfig, builder, wall):
        super().__init__()
        
        self.parent = parent
        self.feature_directory = "features"
        
        self.ui = loader.load(os.path.join(basedir, "addfeaturewindow.ui"), None)
        self.ui.setWindowTitle(app_title)
        
        self.config = config
        self.gconfig = gconfig
        self.builder = builder
        self.wall = wall
        
        # Load features from directory
        self.list_features = self.get_list_features (self.feature_directory)
        #print (f"List features {self.list_features}")
        # Need to create list as
        # QtCore.QAbstractListModel
        self.features_model = QStandardItemModel(self.ui.listView)
        
        for feature in self.list_features:
            item = QStandardItem(feature[1])

            # Add a checkbox to it
            #item.setCheckable(True)

            # Add the item to the model
            self.features_model.appendRow(item)
            
        self.ui.listView.setModel(self.features_model)
        
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.ui.show()
    
    
    def set_wall (self, wall):
        self.wall = wall
    
    def get_list_features (self, directory):
        # currently just get list of files
        # Update to scan contents for titles & types
        file_data = []
        files = os.listdir(directory) 
        for file in files:
            #print (f"File is {file}")
            # Convert into summary indexed by filename
            # Todo load the file read the "name" entry and put it instead of the
            # second entry
            file_data.append ([file,f"{file}"])
        return file_data
    
    
    # Show entire window
    def show(self):
        self.ui.show()
        self.ui.activateWindow()
        self.ui.raise_()
        
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
        
        # New params is the info needed to redo if we undo
        new_params = {
                'feature_file': self.list_features[index_pos][0]
                }
        # Old params are the steps to undo (what the current values are before changing), in this case the feature
        # added so that we can delete it
        old_params = {
            'wall': self.wall,
            'feature': self.wall.features[-1]
            }
        self.parent.history.add(f"Add feature {self.list_features[index_pos][0]}", "Add feature", old_params, new_params)
        
        
        self.parent.update_current_scene()
        self.hide()
        

        

