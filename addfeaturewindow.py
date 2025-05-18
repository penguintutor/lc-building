# Window to add / update wall or roof
# Currently allows creation using different types (eg. rectangle / apex)
# However all are stored and edited as custom
# May change in future, but will need a change in file format as well as how wall.py
# interprets the different types

import os
import json
from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTreeWidget, QTreeWidgetItem
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
        self.feature_dict = self.get_dict_features(self.feature_directory)
        
        items = []
        for key, values in self.feature_dict.items():
            item = QTreeWidgetItem([key])
            for value in values:
                #ext = value.split(".")[-1].upper()
                child = QTreeWidgetItem([value[0], value[1]])
                item.addChild(child)
            items.append(item)

        self.ui.treeWidget.insertTopLevelItems(0, items)
        
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.buttonBox.accepted.connect(self.accept)
        
        self.ui.show()
    
    
    def set_wall (self, wall):
        self.wall = wall
    
    # Gets list of features and stores into a dict
    # Index is the category, and then list of the elements
    def get_dict_features (self, directory):
        # currently just get list of files
        # Update to scan contents for titles & types
        file_data = {}
        files = os.listdir(directory) 
        for file in files:
            file_info = self.read_feature_file_summary (self.feature_directory+"/"+file)
            if not (file_info[1] in file_data):
                file_data[file_info[1]] = [[file_info[0],file_info[2]]]
            else:
                file_data[file_info[1]].append ([file_info[0], file_info[2]])
        return file_data


    # Read summary information from feature file
    # Ie Title and Category - also adds filename to the returned data
    # Returns [title, category, filename]
    def read_feature_file_summary (self, filename):
        try:
            with open(filename, 'r') as datafile:
                feature_data = json.load(datafile)
        except Exception as err:
            print (f"Error {err}")
            return
        # Get the name - otherwise return None
        if 'name' not in feature_data.keys():
            print ("Invalid feature file")
            return None
        return [feature_data['name'], feature_data['type'], filename]
    
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
        
        index = self.ui.treeWidget.selectedIndexes()[0]
            
        parent = index.parent().data()
        child = index.row()
        filename = self.feature_dict[parent][child][1]
        
        # Add this feature
        # (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None):
        self.wall.add_feature_file (filename)
        
        # New params is the info needed to redo if we undo
        new_params = {
                'feature_file': filename
                }
        # Old params are the steps to undo (what the current values are before changing), in this case the feature
        # added so that we can delete it
        old_params = {
            'wall': self.wall,
            'feature': self.wall.features[-1]
            }
        self.parent.history.add(f"Add feature {filename}", "Add feature", old_params, new_params)
        
        self.parent.update_current_scene()
        self.hide()
        
