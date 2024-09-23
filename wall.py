# Wall class with subclasses
# A wall is something that is cut out which could be a wall or a roof
# Can have texures applied or features added

# Create using actual dimensions in mm, then many of the methods return scaled dimensions
import math
from texture import *
from feature import *
from interlocking import Interlocking
from laser import *
from helpers import *
from shapely import Polygon

# Texture is generated as part of get_etch,
# This means that if a feature is added as long as it
# is before get etch, then that part will be removed from
# the etch

# Textures are currently created in walls - may make sense to pull this into a
# separate texture generator class in future

# Interlocking is applied to sides that it is associated with.
# Interlocking starts at bottom left and works along the line
# As such all lines need to be in direction away from bottom left

class Wall():
    
    settings = {}
    
    def __init__ (self, name, points, view="front"):
        self.name = name
        self.points = points
        self.polygon = Polygon(points)
        self.view = view          # Which side to view it on when in the GUI
        #self.max_width = width
        #self.max_height = height
        self.material = "smooth"
        self.il = []              # Interlocking - only one allowed per edge, but multiple allowed on a wall
        self.textures = []        # Typically one texture per wall, but can have multiple if zones used - must not overlap
        self.features = []        # Features for this wall
        # by default are a wall, or could be roof
        self.type = "wall"

    # Get cuts for outside of wall and any inner cuts (eg. features)
    def get_cuts (self):
        cut_edges = []
        # Start at 1 (2nd point) end of first edge
        for i in range(1, len(self.points)):
            cut_edges.append([self.points[i-1], self.points[i]])
        
        # Convert edges into lines
        cut_lines = []
        for i in range(0, len(cut_edges)):
            # Do any interlocks apply to this edge if so apply interlocks
            # copy edge into list for applying transformations
            this_edge_segments = [cut_edges[i]]
            start_line = this_edge_segments[0][0]
            end_line = this_edge_segments[0][1]
            edge_ils = None
            for il in self.il:
                if il.get_edge() == i:
                    # todo add interlocks to this edge
                    edge_ils = il
            # Now sort into order to apply
            # Must not overlap, but only check startpos rather than end
            if edge_ils != None:
                # remove last segment to perform transformations on it
                remaining_edge_segment = this_edge_segments.pop()
                # Then add any returned segments back onto the list
                this_edge_segments.extend(edge_ils.add_interlock_line(start_line, end_line, remaining_edge_segment))
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
    
    # Implement this at the Wall level
    def get_etches (self):
        etches = self._texture_to_etches()
        # Add cuts from features
        feature_etches = self._get_etches_features()
        if feature_etches != None:
            etches.extend(feature_etches)
        return etches

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
    
    # max distance x
    def get_maxwidth (self):
        return self.polygon.bounds[2] - self.polygon.bounds[0]
    
    def get_maxheight (self):
        return self.polygon.bounds[3] - self.polygon.bounds[1]
       
    def add_texture (self, type, area, settings):
        # If no area / zone provided then use wall
        if area == []:
            area = self.points
        self.textures.append(Texture(area, type, settings))

       

    # Add a feature - such as a window
    # cuts, etches and outers should all be lists
    # If not set to None then change to [] avoid dangerous default
    def add_feature (self, startpos, points, cuts=None, etches=None, outers=None):
        # feature number will be next number
        # Will return that assuming that this is successful
        feature_num = len(self.features)
        if cuts == None:
            cuts = []
        if etches == None:
            etches = []
        if outers == None:
            outers = []
        self.features.append(Feature(startpos, points, cuts, etches, outers))
        # If want to handle settings can do so here
        # Eg. support textures
        return feature_num
    
    # add any interlock rules for the edges
    # edges are number from 0 (top left) in clockwise direction
    # parameters should be a dictionary if supplied
    def add_interlocking (self, step, edge, primary, reverse, parameters=None):
        if parameters==None:
            parameters = {}
        self.il.append(Interlocking(step, edge, primary, reverse, parameters))
            
    # This is later stage in get_etches
    def _texture_to_etches(self):
        etches = []
        exclude_areas = []
        for feature in self.features:
            exclude_areas.append(feature.get_points())
        for texture in self.textures:
            # Each texture can have one or more etches
            etches.extend(texture.get_etches(exclude_areas))
        return etches
        

    def _get_cuts_features (self):
        feature_cuts = []
        for feature in self.features:
            feature_cuts.extend(feature.get_cuts())
            if self.settings["outertype"] == "cuts":
                new_cuts = feature.get_outers_cuts()
                if new_cuts != None:
                    feature_cuts.extend(new_cuts)
        return feature_cuts
    
    def _get_etches_features (self):
        feature_etches = []
        for feature in self.features:
            feature_etches.extend(feature.get_etches())
            if self.settings["outertype"] == "etches":
                new_etches = feature.get_outers_etches()
                if new_etches != None:
                    feature_etches.extend(new_etches)
        return feature_etches

