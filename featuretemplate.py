from template import *
import json

# Template for Building.
# Mostly inherits from Template, but allows extra features
# in future regarding validating data

# Template is arranged into dictionaries
# Top level = information about template (name, category, description)
# "defaults" are values that the user may want to change
#    (overall dimensions etc depth, width, wall_height etc.)
# "cuts are used to cutout"
# "etches" used for drawing etch lines etc.
class FeatureTemplate (Template):
    
    def __init__ (self):
        super().__init__()
        
    def get_type (self):
        return "feature"
    
    # Other template functions return the data that is in the template
    # get_cuts and get_etches process the data before returning.
    # returns a different data set this allows values to be recalculated from original if required
    def get_cuts (self):
        return_cuts = []
        for cut in self.json_data["cuts"]:
            # Parse each of the values to see if they match a value
            process_cut = self.process_multiple_tokens(cut[1])
            return_cuts.append((cut[0], process_cut))
        return return_cuts
    
    def get_etches (self):
        pass