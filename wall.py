# Wall class with subclasses
# A wall is something that is cut out which could be a wall or a roof
# Can have texures applied or features added

# Create using actual dimensions in mm, then many of the methods return scaled dimensions
import math
from texture import *
from feature import *

# Texture is generated as part of get_etch,
# This means that if a feature is added as long as it
# is before get etch, then that part will be removed from
# the etch

# Template class - normally use RectWall / ApexWall etc
# scale is divisor to convert from standard to scale size (eg. 76.2 for OO)
class Wall():
    def __init__ (self, width, height):
        self.max_width = width
        self.max_height = height
        self.material = "smooth"
        self.features = []
    
    
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

    def add_feature (self, type, values):
        if type == "window":
            if len(values) > 4:
                cuts = []
                pos = 4
                while pos < len(values):
                    # Must be in groups of 4 (startx, starty, endx, endy)
                    if (len(values) - pos) < 4:
                        break
                    cuts.append((values[pos], values[pos+1], values[pos+2], values[pos+3]))
                    pos += 4
                self.features.append(Window((values[0], values[1]), (values[2], values[3], cuts)))
            else:
                self.features.append(Window((values[0], values[1]), (values[2], values[3])))
                

    # This is later stage in get_etches
    def _texture_to_etch(self, textures):
        etches = []
        for texture in textures:
            # First apply any features exclude areas to textures
            for feature in self.features:
                texture.exclude_etch(*feature.get_area())
            
            
            # Each texture can have one or more etches
            these_etches = texture.get_etches()
            for this_etch in these_etches:
                # convert to pixels
                if this_etch[0] == "rect":
                    etches.append (("rect", (this_etch[1][0], this_etch[1][1]), (this_etch[2][0], this_etch[2][1])))
                if this_etch[0] == "polygon":
                    # convert points into new list of pixel points
                    pixel_points = []
                    for i in range (1, len(this_etch)):
                        pixel_points.append((this_etch[1][i][0], this_etch[1][i][1]))
                        
                    etches.append (("polygon", pixel_points))             
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
        cuts.append (("line", (self.width/2, 0), (0, self.roof_height-self.wall_height)))
        cuts.append (("line", (self.width/2, 0), (self.width, self.roof_height-self.wall_height)))
        # left
        cuts.append (("line", (0, self.roof_height-self.wall_height), (0, self.roof_height)))
        # right
        cuts.append (("line", (self.width, self.roof_height-self.wall_height), (self.width, self.roof_height)))
        cuts.append (("line", (0, self.roof_height), (self.width, self.roof_height)))
        # Add any accessories (windows etc.)
        for feature in self.features:
            cuts.extend(feature.get_cuts())
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
                textures.append (RectTexture((0, y_pos - self.wood_etch), (self.width, self.wood_etch)))
                
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
                    (self.width/2 - half_width_bottom, y_pos)               # bottom left
                    ]))
                
                y_pos -= self.wood_height
                if y_pos < self.wood_height / 4:
                    break
                
        # Apply transformation to sketches
        return self._texture_to_etch(textures)



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
        cuts.append (("rect", (0,0), (self.width, self.height)))
        # Add any accessories (windows etc.)
        for feature in self.features:
            cuts.extend(feature.get_cuts())
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
                textures.append (RectTexture((0, y_pos - self.wood_etch), (self.width, self.wood_etch)))
        # Apply transformation to sketches
        return self._texture_to_etch(textures)
    

    