from template import *
import json

# Template for Building.
# Mostly inherits from Template, but allows extra features
# in future regarding validating data

# Template is arranged into dictionaries
# Top level = information about template (name, category, description)
# "defaults" are values that the user may want to change
#    (overall dimensions etc depth, width, wall_height etc.)
# "typical" are values that are typically left as defined (but can be changed)
#    root_right_overlap, roof_left_overlap etc.
# "walls" list of walls start with front and go around eg. clockwise if viewed from top
# "options are suggested features - uses template names.
#   List of related features
class BuildingTemplate (Template):
    
    def __init__ (self):
        super().__init__()
        
    def get_type (self):
        return "building"