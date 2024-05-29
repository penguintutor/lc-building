# Take template data and store in BuildingData

# Create as an empty class with no data - all empty
# This allows template to be loaded afterwards or for data to be
# Added individually
class BuildingData ():
    def __init__ (self):
        self.data = {}
        pass
    
    # Sets all the data entries - used when loading a template
    # Overwrites all data
    def set_all_data(self, data):
        # Make a copy of the data
        self.data = data.copy()
        
    # Returns the data object
    # May have missing data
    def get_all_data(self):
        return self.data
        
    # Returns top level data as a dictionary
    # Any values not set are returned as empty strings
    # Returns a new copy of the data
    def get_main_data(self):
        return_data = {}
        for key in ["name", "type", "subtype", "description"]:
            if key in self.data:
                return_data[key] = self.data[key]
            else:
                return_data[key] = ""
        return return_data
        
    # Defaults are things that are often changed to get different size of building
    # eg. depth, width, wall_height, roof_height, roof_depth & roof_width
    def get_defaults(self):
        return self.data["defaults"]
    
    # Typical are default values that are not normally changed even if you change shape of building
    #eg. roof_right_overlap / left / front / rear; wood_height, wood_etch
    def get_typical(self):
        return self.data["typical"]
    
    def get_walls(self):
        return self.data["walls"]
    
    # Return combination of defaults and typical values
    def get_values(self):
        return {**self.data["defaults"], **self.data["typical"]}
        #for key in data.keys():
        #    # is this one of the multi-layer categories
        #    if key == "defaults" :
        #        for defaults_key in data['defaults'].keys():
        #            self.data['defaults'][defaults_key] = 
        #    else:
        #        self.data['key']
                    
            