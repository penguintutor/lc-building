# Used for reading, editing and saving buildings
# Uses BuildingData to import the data and then to
# write it out, but otherwise uses internal objects to handle


from buildingdata import *
from lcconfig import LCConfig

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
        #Todo update building at this point
        self.building.save_file(filename)
        
        