# Take template data and store in BuildingData
import json
import re

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
# Views must be one of these or default to front
allowed_views = ["front", "right", "rear", "left", "top", "bottom"]

# Create as an empty class with no data - all empty
# This allows template to be loaded afterwards or for data to be
# Added individually
class BuildingData ():
    def __init__ (self):
        self.data = {}

    
    # Checks the appropriate parameters for a matching value_string then evaluate
    # Returns as string
    # Used by process tokens
    def get_value_str (self, value_string):
        # if number then return directly as string
        if (is_number(value_string)):
            return (value_string)
        if value_string in self.data["parameters"]:
            return str(self.data["parameters"][value_string])
        else:
            return None
    
            
    # Better method to process_tokens which can take a single entry or list
    def process_multiple_tokens (self, token_strings):
        new_list = []
        for this_string in token_strings:
            # if this_string is actually a list then call recursively
            if type(this_string) is list:
                new_list.append(self.process_multiple_tokens (this_string))
            else:
                new_list.append(self.process_token (this_string))
        return new_list
            
    # Processes values from loaded cuts and etches looking for tokens and
    # converts the values relative to existing values
    # returns as string
    def process_token_str (self, token_string):
        new_string = ""
        # Token can be any alphanumeric and _
        # Note include numbers as token including . for fractions
        current_pos = 0
        for m in re.finditer(r"[\w.]+", token_string):
            this_token = m.group(0)
            # replace from start
            start = m.start()
            end = m.end()
            if start > current_pos:
                new_string += token_string[current_pos:start]
            new_string += self.get_value_str(this_token)
            current_pos = end
        # Any remaining chars add to the end
        if len(token_string) > current_pos:
            new_string += token_string[current_pos:]
        return new_string
        
    # Process token and perform eval to return as a number
    def process_token (self, token_string):
        new_string = self.process_token_str(token_string)
        value = eval(new_string)
        return value
    
    # Load a data file
    # Overrides all data in memory
    def load_file (self, filename):
        # Keep reference to filename loaded
        self.filename = filename
        with open(filename, 'r') as datafile:
            self.data = json.load(datafile)
            
    
    # Save current data to file
    # Overwrites existing file
    def save_file (self, filename):
        # Updates filename with new filename
        self.filename = filename
        json_data = json.dumps(self.data)
        with open(filename, 'w') as datafile:
            datafile.write(json_data)
            
    
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
    
    # Get wall information processing tokens
    def get_walls(self):
        wall_data = []
        for wall in self.data["walls"]:
            # Basic error check for minimum number of parameters
            if (len(wall) < 2):
                wall_data.append (("Error", [[0,0],[0,0],[0,0],[0,0]], "front"))
            # View is optional parameter 2 (default to front)
            if (len(wall) < 3 or wall[2] not in allowed_views):
                view = "front"
            else:
                view = wall[2]
            wall_data.append((wall[0], self.process_multiple_tokens(wall[1]), view))
        return wall_data
    
    def get_interlocking(self):
        return self.data["interlocking"]
    
    # Returns roofs after parsing tokens
    def get_roofs(self):
        roof_data = []
        for roof in self.data["roofs"]:
            # Basic error check for minimum number of parameters
            if (len(roof) < 2):
                roof_data.append(("Error", [[0,0],[0,0],[0,0],[0,0]], "front"))
            # View is optional parameter 2 (default to top for roof)
            if (len(roof) < 3 or roof[2] not in allowed_views):
                view = "top"
            else:
                view = roof[2]
            roof_data.append((roof[0], self.process_multiple_tokens(roof[1]), view))
        return roof_data
    
    def get_textures(self):
        return self.data["textures"]
    
    # Returns as a copy of the parameters and settings
    def get_values(self):
        values = self.data["parameters"].copy()
        # If any settings then add those
        if "settings" in self.data.keys():
            values.update(self.data["settings"])
        return values

    def get_features(self):
        return self.data["features"]
    
    # Returns the roof overlap values as a dict
    def get_roof_overlap(self):
        # Check each entry exists, otherwise return 0 as the value
        overlap_dict = {}
        if "roof_right_overlap" in self.data["parameters"].keys():
            overlap_dict["right"] = self.data["parameters"]["roof_right_overlap"]
        else:
            overlap_dict["right"] = 0
        if "roof_left_overlap" in self.data["parameters"].keys():
            overlap_dict["left"] = self.data["parameters"]["roof_left_overlap"]
        else:
            overlap_dict["left"] = 0
        if "roof_front_overlap" in self.data["parameters"].keys():
            overlap_dict["front"] = self.data["parameters"]["roof_front_overlap"]
        else:
            overlap_dict["front"] = 0
        if "roof_rear_overlap" in self.data["parameters"].keys():
            overlap_dict["rear"] = self.data["parameters"]["roof_rear_overlap"]
        else:
            overlap_dict["rear"] = 0
        return overlap_dict