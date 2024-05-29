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