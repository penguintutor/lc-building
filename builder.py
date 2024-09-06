# Used for reading, editing and saving buildings

from buildingdata import *
from config import LCConfig

class Builder():
    def __init__(self, lcconfig):
        self.config = lcconfig
        
        # Create empty building data instance
        self.building = BuildingData()

    # Loads a new file overwriting all data
    def load_file(self, filename):
        self.building.load_file(filename)
        
    # Saves the file
    # Overwrites existing file
    # If want to confirm to overwrite check before calling this
    def save_file(self, filename):
        self.building.save_file(filename)
        
        