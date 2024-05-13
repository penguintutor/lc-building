# Wall class with subclasses
# A wall is something that is cut out which could be a wall or a roof
# Can have texures applied or features added

# Create using actual dimensions in mm, then many of the methods return scaled dimensions
import math
from texture import *


mm_to_pixels = 3.543307

# Template class - normally use RectWall
# scale is divisor to convert from standard to scale size (eg. 76.2 for OO)
class Wall():
    def __init__ (self, width, height, scale):
        self.max_width = width
        self.max_height = height
        self.scale = scale
        self.material = "smooth"
    
    def to_pixels (self, mm_value):
        return (mm_value / self.scale) * mm_to_pixels
    
    def get_scale_maxsize (self):
        return (self.get_scale_maxwidth(), self.get_scale_maxheight())
    
    def get_scale_maxwidth (self):
        return self.to_pixels(self.max_width)
    
    def get_scale_maxheight (self):
        return self.to_pixels(self.max_height)
    
    # Etching is created later, this defines settings
    def add_wood_etch (self, wood_height, wood_etch):
        self.material = "wood"
        self.wood_height = wood_height
        self.wood_etch = wood_etch
        
        
class ApexWall(Wall):
    def __init__ (self, width, roof_height, wall_height, scale):
        super().__init__(width, roof_height, scale)
        self.width = width
        self.roof_height = roof_height
        self.wall_height = wall_height

    # Return all cuts as tuples shapestype followed by dimensions
    # Start from 0,0
    def get_scale_cuts (self):
        cuts = []
        #top centre to left
        cuts.append (("line", (self.to_pixels(self.width/2), 0), (0, self.to_pixels(self.roof_height-self.wall_height))))
        cuts.append (("line", (self.to_pixels(self.width/2), 0), (self.to_pixels(self.width), self.to_pixels(self.roof_height-self.wall_height))))
        # left
        cuts.append (("line", (0, self.to_pixels(self.roof_height-self.wall_height)), (0, self.to_pixels(self.roof_height))))
        # right
        cuts.append (("line", (self.to_pixels(self.width), self.to_pixels(self.roof_height-self.wall_height)), (self.to_pixels(self.width), self.to_pixels(self.roof_height))))
        cuts.append (("line", (0, self.to_pixels(self.roof_height)), (self.to_pixels(self.width), self.to_pixels(self.roof_height))))
        # Add any accessories (windows etc.)       
        return cuts
    
    def get_scale_etches (self):
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
        ## Todo
        
        etches = []
        for texture in textures:
            this_etch = texture.get_etch()
            # convert to pixels
            if this_etch[0] == "rect":
                etches.append (("rect", (self.to_pixels(this_etch[1][0]), self.to_pixels(this_etch[1][1])), (self.to_pixels(this_etch[2][0]), self.to_pixels(this_etch[2][1]))))
            if this_etch[0] == "polygon":
                # convert points into new list of pixel points
                pixel_points = []
                for i in range (1, len(this_etch)):
                    pixel_points.append((self.to_pixels(this_etch[1][i][0]), self.to_pixels(this_etch[1][i][1]))) 
                    
                etches.append (("polygon", pixel_points)) 
            
        return etches



# Standard rectangle - inherits most methods
class RectWall(Wall):
    def __init__ (self, width, height, scale=1):
        super().__init__(width, height, scale)
        self.width = width
        self.height = height
        
    # Return all cuts as tuples shapestype followed by dimensions
    # Start from 0,0
    def get_scale_cuts (self):
        cuts = []
        # frame as rectangle
        cuts.append (("rect", (0,0), (self.to_pixels(self.width), self.to_pixels(self.height))))
        # Add any accessories (windows etc.)       
        return cuts
    
    def get_scale_etches (self):
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
        # Apply transformations to textures
        ## Todo
        
        # Convert textures into etches
        etches = []
        for texture in textures:
            this_etch = texture.get_etch()
            # convert to pixels
            if this_etch[0] == "rect":
                etches.append (("rect", (self.to_pixels(this_etch[1][0]), self.to_pixels(this_etch[1][1])), (self.to_pixels(this_etch[2][0]), self.to_pixels(this_etch[2][1]))))

        #etches.append (("rect", (0, (self.to_pixels(y_pos - self.wood_etch))), (self.to_pixels(self.width), self.to_pixels(self.wood_etch))))
        return etches
    

    