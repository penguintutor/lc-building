# Wall class with subclasses
# A wall is something that is cut out which could be a wall or a roof
# Can have texures applied or features added

# Create using actual dimensions in mm, then many of the methods return scaled dimensions
import math
from texture import *
from feature import *
from interlocking import Interlocking
from laser import *

def get_angle (line):
    dx = line[1][0] - line[0][0]
    dy = line[1][1] - line[0][1]
    theta = math.atan2(dy, dx)
    angle = math.degrees(theta)  
    if angle < 0:
        angle = 360 + angle
    return angle

# Work out if mainly in x direction or mainly in y
# based on angle of line
def get_mainly_xy (line):
    angle = get_angle (line)
    if angle <= 45 or (angle >=135 and angle <=225) or angle >= 315:
        return "x"
    else:
        return "y"

# Texture is generated as part of get_etch,
# This means that if a feature is added as long as it
# is before get etch, then that part will be removed from
# the etch

# Textures are currently created in walls - may make sense to pull this into a
# separate texture generator class in future

# Interlocking is applied to sides that it is associated with.
# Interlocking starts at bottom left and works along the line
# As such all lines need to be in direction away from bottom left

# Abstract class - normally use RectWall / ApexWall etc
# scale is divisor to convert from standard to scale size (eg. 76.2 for OO)
class Wall():
    def __init__ (self, width, height):
        self.max_width = width
        self.max_height = height
        self.material = "smooth"
        self.features = []        # Features for this wall
        self.il = []              # Interlocking - one for each type of interlock (can have multiple per edge)
        # by default are a wall, or could be roof
        self.type = "wall"
        # default to "cuts" - can be "etches"
        # todo move this to a setting that can be changed by the user
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
       
    def add_texture (self, type, settings):
        if type == "wood":
            self.add_wood_etch(settings["wood_height"], settings["wood_etch"])
       
    # Etching is created later, this defines settings
    def add_wood_etch (self, wood_height, wood_etch):
        self.material = "wood"
        self.wood_height = wood_height
        self.wood_etch = wood_etch

    # Add a feature - such as a window
    # cuts, etches and outers should all be lists
    # If not set to None then change to [] avoid dangerous default
    def add_feature (self, startpos, size, cuts=None, etches=None, outers=None):
        # feature number will be next number
        # Will return that assuming that this is successful
        feature_num = len(self.features)
        if cuts == None:
            cuts = []
        if etches == None:
            etches = []
        if outers == None:
            outers = []
        self.features.append(Feature(startpos, size, cuts, etches, outers))
        # If want to handle settings can do so here
        # Eg. support textures
        return feature_num
    
    # add any interlock rules for the edges
    # edges are number from 0 (top left) in clockwise direction
    # parameters should be a dictionary if supplied
    def add_interlocking (self, step, edge, primary, parameters=None):
        if parameters==None:
            parameters = {}
        self.il.append(Interlocking(step, edge, primary, parameters))
            
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
        
        
    def _rect_to_edges (self, width, height):
        # lines are list of start / end - convert to CutLines later
        # Start is 0, 0 (as this is the wall)
        # Edges start with top left point and got clockwise
        return [
            [(0,0), (width, 0)],
            [(width,0), (width, height)],
            [(width, height), (0, height)],
            [(0, height), (0,0)]
            ]
        

    # Get cuts if a rectangular walls
    def get_cuts_rect (self):
        cut_lines = []
        # If width & height defined use those
        # otherwise use max_width & max_height
        if hasattr(self, "width"):
            width = self.width
        else:
            width = self.max_width
        if hasattr(self, "height"):
            height = self.height
        else:
            height = self.max_height
        # If wall does not have interlocking
        if self.il == []:
            return self._get_cuts_rect_only(width, height)
        # otherwise we convert to lines then handle interlocking
        cut_edges = self._rect_to_edges(width, height)
        # Add interlocking each edge at a time
        for i in range(0, len(cut_edges)):
            # Do any interlocks apply to this edge if so apply interlocks
            # copy edge into list for applying transformations
            this_edge_segments = [cut_edges[i]]
            start_line = this_edge_segments[0][0]
            end_line = this_edge_segments[0][1]
            edge_ils = []
            for il in self.il:
                if il.get_edge() == i:
                    # todo add interlocks to this edge
                    edge_ils.append(il)
            # Now sort into order to apply
            # Must not overlap, but only check startpos rather than end
            if edge_ils != []:
                sorted_ils = sorted(edge_ils)
                # Now apply each interlocking in turn
                for this_ils in sorted_ils:
                    # remove last segment to perform transformations on it
                    remaining_edge_segment = this_edge_segments.pop()
                    # Then add any returned segments back onto the list
                    this_edge_segments.extend(this_ils.add_interlock_line(start_line, end_line, remaining_edge_segment))
                # Convert to line objects
                for this_segment in this_edge_segments:
                    cut_lines.append(CutLine(this_segment[0], this_segment[1]))
            else:
                # otherwise just append his one edge
                cut_lines.append(CutLine(cut_edges[i][0], cut_edges[i][1]))
        # Add cuts from features
        feature_cuts = self._get_cuts_features()
        if feature_cuts != None:
            cut_lines.extend(feature_cuts)
        return cut_lines
        
    def _get_cuts_features (self):
        feature_cuts = []
        for feature in self.features:
            feature_cuts.extend(feature.get_cuts())
            if self.outer_type == "cuts":
                new_cuts = feature.get_outers_cuts()
                if new_cuts != None:
                    feature_cuts.extend(new_cuts)
        return feature_cuts

    # Get cuts if rectangular wall
    # And confirmed not interlocking
    def _get_cuts_rect_only (self, width, height):
        cuts = []
        # frame as rectangle
        cuts.append (CutRect((0,0), (width, height)))
        # Add any accessories (windows etc.)
        feature_cuts = self._get_cuts_features()
        if feature_cuts != None:
            cuts.extend(feature_cuts)
        return cuts

        
class WallApex(Wall):
    def __init__ (self, width, roof_height, wall_height):
        super().__init__(width, roof_height)
        self.width = width
        self.roof_height = roof_height
        self.wall_height = wall_height
        

    # Return all cuts as tuples shapestype followed by dimensions
    # Start from 0,0
    # edges are numbered from top centre going clockwise
    def get_cuts (self):
        cuts = []          # First create each line in cuts list
        cut_lines = []     # Then when add interlocking turn into cut_lines
        # top to centre
        cuts.append ([(0, self.roof_height-self.wall_height), (self.width/2, 0)])
        # top centre to right
        cuts.append ([(self.width/2, 0), (self.width, self.roof_height-self.wall_height)])
        #right
        cuts.append ([(self.width, self.roof_height-self.wall_height), (self.width, self.roof_height)])
        #bottom
        cuts.append ([(self.width, self.roof_height), (0, self.roof_height)])
        #left
        cuts.append ([(0, self.roof_height), (0, self.roof_height-self.wall_height)])
        # Apply any interlocks to each of the edges
        for i in range(0, len(cuts)):
            # Do any interlocks apply to this edge if so apply interlocks
            # copy edge into list for applying transformations
            this_edge_segments = [cuts[i]]
            start_line = this_edge_segments[0][0]
            end_line = this_edge_segments[0][1]
            edge_ils = []
            for il in self.il:
                if il.get_edge() == i:
                    # todo add interlocks to this edge
                    edge_ils.append(il)
            # Now sort into order to apply
            # Must not overlap, but only check startpos rather than end
            if edge_ils != []:
                sorted_ils = sorted(edge_ils)
                # Now apply each interlocking in turn
                for this_ils in sorted_ils:
                    # remove last segment to perform transformations on it
                    remaining_edge_segment = this_edge_segments.pop()
                    # Then add any returned segments back onto the list
                    this_edge_segments.extend(this_ils.add_interlock_line(start_line, end_line, remaining_edge_segment))
                # Convert to line objects
                for this_segment in this_edge_segments:
                    cut_lines.append(CutLine(this_segment[0], this_segment[1]))
            # If not interlocking on this line then append here
            else:
                cut_lines.append(CutLine(start_line, end_line))
                    
        # Add any accessories (windows etc.)
        for feature in self.features:
            cut_lines.extend(feature.get_cuts())
            if self.outer_type == "cuts":
                cut_lines.extend(feature.get_outers_cuts())
        return cut_lines
    
    # Apply the etches to the wall
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
                # Subtract the etch thickness
                y_pos -= self.wood_etch
                
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
                
                y_pos -= (self.wood_height + self.wood_etch)
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
class WallRect(Wall):
    def __init__ (self, width, height):
        super().__init__(width, height)
        self.width = width
        self.height = height
        
    # Return all cuts as tuples shapestype followed by dimensions
    # Start from 0,0
    def get_cuts (self):
        return self.get_cuts_rect()
    
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
                # Subtract the etch distance
                y_pos -= self.wood_etch
        # Apply transformation to sketches
        etches = self._texture_to_etches(textures)
        # Add any features
        for feature in self.features:
            etches.extend(feature.get_etches())
            if self.outer_type == "etches":
                etches.extend(feature.get_outers_etches())
        return etches

# Roofs are a type of wall
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

class RoofApexLeft(Wall):
    def __init__ (self, width, depth, height_difference, overlaps):
        self.roof_width = width+overlaps["rear"]+overlaps["front"]
        # provided depth is flat, so adjust for height difference
        self.roof_depth = math.sqrt (depth **2 + height_difference **2) + overlaps["right"]
        # roof_depth translates into wall height for when outputting (width, height)
        super().__init__(self.roof_width, self.roof_depth)
        
    # Cuts are standard rectangle
    def get_cuts (self):
        return self.get_cuts_rect()
    
    # Currently returns empty list - plain roof
    def get_etches (self):
        return []
        
class RoofApexRight(Wall):
    def __init__ (self, width, depth, height_difference, overlaps):
        self.roof_width = width+overlaps["rear"]+overlaps["front"]
        # provided depth is flat, so adjust for height difference
        self.roof_depth = math.sqrt (depth **2 + height_difference **2) + overlaps["left"]
        # roof_depth translates into wall height for when outputting (width, height)
        super().__init__(self.roof_width, self.roof_depth)
        
    def get_cuts (self):
        return self.get_cuts_rect()
    
    # Currently returns empty list - plain roof
    def get_etches (self):
        return []

class RoofFlat(Wall):
    def __init__ (self, width, depth, height_difference, overlaps):
        self.roof_width = width+overlaps["rear"]+overlaps["front"]
        # provided depth is flat, so adjust for height difference
        self.roof_depth = math.sqrt (depth **2 + height_difference **2) + overlaps["right"] + overlaps["left"]
        # roof_depth translates into wall height for when outputting (width, height)
        super().__init__(self.roof_width, self.roof_depth)
        
    def get_cuts (self):
        return self.get_cuts_rect()
    
    # Currently returns empty list - plain roof
    def get_etches (self):
        return []
