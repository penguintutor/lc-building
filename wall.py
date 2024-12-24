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

# Note that methods ending _towall should only be used during a load or where update is being called afterwards
# Is used internally and for performance reasons can be used by file load etc.

class Wall():
    
    settings = {}
    
    def __init__ (self, name, points, view="front", position=[0,0]):
        # type is set as a wall - but allows us to check as may have different type
        # in future (eg. "exterior_object" - which could be porch support or something similar)
        self.type = "wall"
        self.name = name
        self.points = points
        self.polygon = Polygon(points)
        self.view = view          # Which side to view it on when in the GUI
        self.position = position  # position within GUI scenese
        #print (f"Position {self.position}")
        #self.max_width = width
        #self.max_height = height
        self.show_interlock = False # Do we show interlocking - set using update
        self.material = "smooth"
        self.il = []              # Interlocking - only one allowed per edge, but multiple allowed on a wall
        self.textures = []        # Typically one texture per wall, but can have multiple if zones used - must not overlap
        self.features = []        # Features for this wall
        # by default are a wall, or could be roof - in future wall & roof are same
        # type will likely be used for different ways of creating a wall (eg. rectangle vs apex)
        #self.type = "wall"
        # Move these to variables so that they are cached within the wall class
        # Only update when update_xxx is called
        # These are for all features and textures - can get separately using get_wall_cuts / etches etc.
        # Which will generate as needed rather than for the whole object
        self.cut_lines = []
        self.etches = []
        self.outers = []
        self.update()
        
    def get_features (self):
        return self.features
    
    def get_textures (self):
        return self.textures


    # Updates cuts, etches and outers
    # Interlock = None, keep current, otherwise update
    def update (self, interlock=None):
        if interlock != None:
            self.show_interlock = interlock
        self.update_cuts()
        self.update_etches()
        self.update_outers()
        
    # Gets only cuts associated with the wall itself (not features / textures)
    # Used by wall edit also internally by update_cuts
    def get_wall_cuts (self):
        #print ("Getting wall cuts")
        # First get edges then generate cuts
        # cut lines is the one that is returned
        # this can either be used directly (eg. in edit wall)
        # or saved into self.cut_lines through an update
        cut_edges = []
        cut_lines = []
        # Start at 1 (2nd point) end of first edge
        for i in range(1, len(self.points)):
            cut_edges.append([self.points[i-1], self.points[i]])
        
        # Convert edges into lines
        for i in range(0, len(cut_edges)):
            #print ("Converting edges into lines")
            # Do any interlocks apply to this edge if so apply interlocks
            # copy edge into list for applying transformations
            this_edge_segments = [cut_edges[i]]
            start_line = this_edge_segments[0][0]
            end_line = this_edge_segments[0][1]
            edge_ils = None
            
            # Only handle interlocking if not False
            if (self.show_interlock == True):
                for il in self.il:
                    if il.get_edge() == i:
                        # add interlocks to this edge
                        edge_ils = il
                        
            # Now sort into order to apply
            # Must not overlap, but only check startpos rather than end
            # Note if interlock = false then we don't have added any edge_ils so don't need to check here
            if edge_ils != None:
                # remove last segment to perform transformations on it
                remaining_edge_segment = this_edge_segments.pop()
                # Then add any returned segments back onto the list
                this_edge_segments.extend(edge_ils.add_interlock_line(start_line, end_line, remaining_edge_segment))
                # Convert to line objects
                for this_segment in this_edge_segments:
                    cut_lines.append(CutLine(this_segment[0], this_segment[1]))
                    #print (f" Adding il segment {i} {this_segment[0]} , {this_segment[1]}")
            else:
                # otherwise just append his one edge
                cut_lines.append(CutLine(cut_edges[i][0], cut_edges[i][1]))
                #print (f"  Adding normal edge {i} : {cut_edges[i][0]} , {cut_edges[i][1]}")
        return cut_lines
                

    # Generate all the cuts and store in self.cuts
    # For performance reasons call this initially then just use get_cuts
    # but if update then run this again before running get_cuts
    def update_cuts (self):
        self.cut_lines = self.get_wall_cuts ()
        # Add cuts from features
        feature_cuts = self._get_cuts_features()
        if feature_cuts != None:
            self.cut_lines.extend(feature_cuts)
        return self.cut_lines
        

    # Get cuts for outside of wall and any inner cuts (eg. features)
    def get_cuts (self):
        return self.cut_lines
    
    def get_etches (self):
        return self.etches
    
    def get_texture_etches (self):
        return self._texture_to_etches()
    
    # Implement this at the Wall level
    def update_etches (self):
        self.etches = self._texture_to_etches()
        # Add etches from features
        feature_etches = self._get_etches_features()
        if feature_etches != None:
            self.etches.extend(feature_etches)
        return self.etches

    def get_outers (self):
        return self.outers
        
    def update_outers (self):
        self.outers = []
        # Add any accessories (windows etc.)
        for feature in self.features:
            self.outers.extend(feature.get_outers())
        return self.outers
    
    def get_type (self):
        return self.type
    
    def get_size_string (self):
        return (f"{int(self.get_maxwidth()):,d}mm x {int(self.get_maxheight()):,d}mm")
    
    def get_maxsize (self):
        return (self.get_maxwidth(), self.get_maxheight())
    
    # max distance x
    def get_maxwidth (self):
        return self.polygon.bounds[2] - self.polygon.bounds[0]
    
    def get_maxheight (self):
        return self.polygon.bounds[3] - self.polygon.bounds[1]
       
    
    def add_texture_towall (self, type, area, settings):
        # If no area / zone provided then use wall
        if area == []:
            area = self.points
        # reordered here when passed to constructor
        self.textures.append(Texture(area, type, settings))
        
    # Note that this is different order to texture constructor as
    # in constructor type is optional - but not in here
    def add_texture (self, type, area, settings):
        self.add_texture_towall (type, area, settings)
        # Only update etches as that is limit of textures
        self.update_etches()

    # This is internal method - or one to be used when loading from file
    # Does not perform update - also used by add_feature but then performs update
    # If using this then must perform update after loading
    def add_feature_towall (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None):
        # feature number will be next number
        # Will return that assuming that this is successful
        feature_num = len(self.features)
        if cuts == None:
            cuts = []
        if etches == None:
            etches = []
        if outers == None:
            outers = []
        self.features.append(Feature(feature_type, feature_template, startpos, points, cuts, etches, outers))
        # If want to handle settings can do so here
        # Eg. support textures
        # Update the wall
        self.update()
        return feature_num

    # Add a feature - such as a window
    # cuts, etches and outers should all be lists
    # If not set to None then change to [] avoid dangerous default
    def add_feature (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None):
        feature_num = self.add_feature_towall (feature_type, feature_template, startpos, points, cuts, etches, outers)
        self.update()
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

