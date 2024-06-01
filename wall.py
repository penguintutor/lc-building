# Wall class with subclasses
# A wall is something that is cut out which could be a wall or a roof
# Can have texures applied or features added

# Create using actual dimensions in mm, then many of the methods return scaled dimensions
import math
from texture import *
from feature import *
from laser import *

# Texture is generated as part of get_etch,
# This means that if a feature is added as long as it
# is before get etch, then that part will be removed from
# the etch

# Textures are currently created in walls - may make sense to pull this into a
# separate texture generator class in future

# Abstract class - normally use RectWall / ApexWall etc
# scale is divisor to convert from standard to scale size (eg. 76.2 for OO)
class Wall():
    def __init__ (self, width, height):
        self.max_width = width
        self.max_height = height
        self.material = "smooth"
        self.features = []
        # by default are a wall, or could be roof
        self.type = "wall"
        # default to cuts
        self.outer_type = "cuts"
        
    def get_outers (self):
        outers = []
        # Add any accessories (windows etc.)
        for feature in self.features:
            outers.extend(feature.get_outers())
        return outers
    
    def get_type (self):
        return self.type
    
    def get_maxsize (self):
        return (self.get_maxwidth(), self.get_maxheight())
    
    def get_maxwidth (self):
        return self.max_width
    
    def get_maxheight (self):
        return self.max_height
       
    # Etching is created later, this defines settings
    def add_wood_etch (self, wood_height, wood_etch):
        self.material = "wood"
        self.wood_height = wood_height
        self.wood_etch = wood_etch

    # Add a feature - such as a window
    # Values are startx, starty, endx, endy
    ##### Settings is likely to be deprecated - previous feature commented out
    ##### Settings is dict of settings eg. {"windowtype":"rect"} for basic rectangle window
    def add_feature (self, startpos, size, cuts=[], etches=[], outers=[]):
        # feature number will be next number
        # Will return that assuming that this is successful
        feature_num = len(self.features)
        self.features.append(Feature(startpos, size, cuts, etches, outers))
        # If want to handle settings can do so here
        # Eg. support textures
        return feature_num
            
    # This is later stage in get_etches
    def _texture_to_etches(self, textures):
        etches = []
        for texture in textures:
            # First apply any features exclude areas to textures
            for feature in self.features:
                texture.exclude_etch(*feature.get_area())
            # Each texture can have one or more etches
            etches.extend(texture.get_etches())
        return etches
            

        
class ApexWall(Wall):
    def __init__ (self, width, roof_height, wall_height):
        super().__init__(width, roof_height)
        self.width = width
        self.roof_height = roof_height
        self.wall_height = wall_height
        

    # Return all cuts as tuples shapestype followed by dimensions
    # Start from 0,0
    def get_cuts (self):
        cuts = []
        #top centre to left
        cuts.append (CutLine((self.width/2, 0), (0, self.roof_height-self.wall_height)))
        cuts.append (CutLine((self.width/2, 0), (self.width, self.roof_height-self.wall_height)))
        # left
        cuts.append (CutLine((0, self.roof_height-self.wall_height), (0, self.roof_height)))
        # right
        cuts.append (CutLine((self.width, self.roof_height-self.wall_height), (self.width, self.roof_height)))
        cuts.append (CutLine((0, self.roof_height), (self.width, self.roof_height)))
        # Add any accessories (windows etc.)
        for feature in self.features:
            cuts.extend(feature.get_cuts())
            if self.outer_type == "cuts":
                cuts.extend(feature.get_outers_cuts())
        return cuts
    
    def get_etches (self):
        textures = []
        if self.material == "wood":
            # mark wood joins
            # Start from bottom
            y_pos = self.roof_height
            while (y_pos > 0):
                # move up wood height
                y_pos -= self.wood_height
                # if too small then let that wood be bigger
                if y_pos < self.roof_height - self.wall_height:
                    break
                # Add a rectangle
                textures.append (RectTexture((0, y_pos - self.wood_etch), (self.width, self.wood_etch), direction="horizontal"))
                
            # Continue to top of apex
            # Start by calculating angle of roof
            angle=math.atan((self.roof_height-self.wall_height)/(self.width/2))

            while (y_pos > 0):
                # y_pos is currently in the apex so draw first edge
                # Need the x_pos of top and bottom of the edge - based on right angle triangle
                half_width_bottom = y_pos / math.tan(angle)
                #half_width_top = (y_pos-self.wood_etch) / math.sin(angle)
                half_width_top = (y_pos-self.wood_etch) / math.tan(angle)
                
                # create polygon
                textures.append (TrapezoidTexture([
                    (self.width/2 - half_width_top, y_pos-self.wood_etch),  # top left
                    (self.width/2 + half_width_top, y_pos-self.wood_etch),  # top right
                    (self.width/2 + half_width_bottom, y_pos),              # bottom right
                    (self.width/2 - half_width_bottom, y_pos)              # bottom left
                    ],
                    direction = "horizontal"
                    ))
                
                y_pos -= self.wood_height
                if y_pos < self.wood_height / 4:
                    break
                
        # Apply transformation to sketches
        etches = self._texture_to_etches(textures)
        # Add any features
        for feature in self.features:
            etches.extend(feature.get_etches())
            if self.outer_type == "etches":
                etches.extend(feature.get_outers_etches())
        return etches



# Standard rectangle - inherits most methods
class RectWall(Wall):
    def __init__ (self, width, height):
        super().__init__(width, height)
        self.width = width
        self.height = height
        
    # Return all cuts as tuples shapestype followed by dimensions
    # Start from 0,0
    def get_cuts (self):
        cuts = []
        # frame as rectangle
        cuts.append (CutRect((0,0), (self.width, self.height)))
        # Add any accessories (windows etc.)
        for feature in self.features:
            cuts.extend(feature.get_cuts())
            if self.outer_type == "cuts":
                new_cuts = feature.get_outers_cuts()
                if new_cuts != None:
                    cuts.extend(new_cuts)
        return cuts
    
    def get_etches (self):
        # First apply textures
        textures = []
        if self.material == "wood":
            # mark wood joins
            # Start from bottom
            y_pos = self.height
            while (y_pos > 0):
                # move up wood height
                y_pos -= self.wood_height
                # if too small then let that wood be bigger
                if y_pos < self.wood_height / 4:
                    break
                # Add a rectangle
                textures.append (RectTexture((0, y_pos - self.wood_etch), (self.width, self.wood_etch), direction="horizontal"))
        # Apply transformation to sketches
        etches = self._texture_to_etches(textures)
        # Add any features
        for feature in self.features:
            etches.extend(feature.get_etches())
            if self.outer_type == "etches":
                etches.extend(feature.get_outers_etches())
        return etches

# Roof wall is used for a roof - like a wall
# In future may need to handle different, but for now it's sale as a RectWall
# Actually implemented as a wall
# For type = "apex" then roof is half of shed - but width is still width of building
# Type can be flat (actually still sloping, but one whole roof)
# Or apex (two identical apex segments - create two instances if you want it printed twice)
# or apexleft, apexright if dimensions are different
# For apex if left and right are different then average both, for each sides
# Note that apexleft and apexright still need right and left overlap even though one is ignored
# handled internally as calculated in constructor
# Note setting depth, then querying depth may result in different value (same with width)
# Height difference is not stored - just used in calculation
# Overlap is the distance to extend the roof by, not the actual distance it sticks out from the width of the building
class RoofWall (RectWall):
    def __init__ (self, depth, width, height_difference, type, right_overlap, left_overlap, front_overlap, rear_overlap):
        roof_depth = depth + front_overlap + rear_overlap
        roof_width = width # Most likely this will be replaced
        if type == "flat":
            roof_width = math.sqrt (width ** 2 + height_difference **2) + right_overlap + left_overlap
        if type == "apex":
            roof_width = math.sqrt ((width / 2) ** 2 + height_difference **2) + ((right_overlap + left_overlap)/2)
        # Although init is for width, height enter as depth, width
        # As that will ensure any texture goes the right way
        super().__init__(roof_depth, roof_width)
        self.type = "roof"
    