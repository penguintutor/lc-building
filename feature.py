# A feature is always something that is part of a wall - eg. a door or a window
# Or a roof (which is treated as a type of wall)
# Different to an "extra" which is cut separately (eg. decoration that is mounted afterwards)
from laser import *
from laserfactory import *
from shapely import Polygon

# Each cut is defined in templates (and building data)
# Cut type (eg. rect) followed by list containing strings or values (must work with eval string after subsitution)
# "rect" [x, y, width, height]
# Features must NOT overlap - unpredictable results in textures if do
# Note points should exclude startpos
class Feature():
    lf = LaserFactory()
    # x, y is top left
    # points is a polygon to represent exclude areas
    def __init__ (self, feature_type, feature_template, startpos, points, cuts=[], etches=[], outers=[]):
        self.type = feature_type
        self.template = feature_template
        self.min_x = startpos[0]
        self.min_y = startpos[1]
        # avoid access points directly - as doesn't take into consideration startpos
        # instea use get_exclude() which returns points with min_x, min_y applied
        self.points = points
        # Maintain history of actions for future undo - not currently supported - todo
        # History is a list of lists - each entry [action (eg. move), old data (eg. points)]
        self.history = []
        # Cuts needs to be converted into laser cut objects
        self.cuts = []
        for cut in cuts:
            if cut == []:
                break
            # If already a cut object (eg. CutRect) then add directly
            if isinstance(cut, Cut):
                self.cuts.append(cut)
            else:
                # if not then create a cut object using the laser factory
                self.cuts.append(Feature.lf.create_cut(cut[0], cut[1], (self.min_x, self.min_y)))
        # Do the same for etches
        self.etches = []
        for etch in etches:
            if etch == []:
                break
            # If already an etch object (eg. EtchRect) then add directly
            if isinstance(etch, Etch):
                self.etches.append(etch)
            else:
                # if not then create an etch object using the laser factory
                # strength is etch [2] - optional
                # etch should have parameter offset before strength, so if strength set offset to (0,0)
                if len(etch)>2:
                    self.etches.append(Feature.lf.create_etch(etch[0], etch[1], (self.min_x, self.min_y), etch[2]))
                else:
                    self.etches.append(Feature.lf.create_etch(etch[0], etch[1], (self.min_x, self.min_y)))
        self.outers = []
        for outer in outers:
            if outer == []:
                break
            # If already an outer object (eg. OuterRect) then add directly
            if isinstance(outer, Outer):
                self.outers.append(outer)
            else:
                # if not then create a outer object using the laser factory
                self.outers.append(Feature.lf.create_outer(outer[0], outer[1], (self.min_x, self.min_y)))
        
    def __str__(self):
        return f"Feature: {self.type}"
    
    def get_pos (self):
        return [self.min_x, self.min_y]
    
    # Don't have a name - return template instead
    def get_summary (self):
        return f"{self.type} - {self.template}"
    
        # Returns summary of wall as a dictionary
    def get_summary_dict(self):
        summary_dict = {
            "Feature": self.template,
            "Type": self.type,
            "Size": self.get_size_string()
            }
        return summary_dict
    
    def get_size_string (self):
        return (f"{int(self.get_maxwidth()):,d}mm x {int(self.get_maxheight()):,d}mm")

    def get_max_x (self):
        return self.min_x + self.get_maxwidth()
    
    def get_max_y (self):
        return self.min_y + self.get_maxheight()
    
    def get_mid_x (self):
        return self.min_x + (self.get_maxwidth()/2)
    
    def get_mid_y (self):
        return self.min_y + (self.get_maxheight()/2)

    def get_maxsize (self):
        return (self.get_maxwidth(), self.get_maxheight())
    
    # Move so that the max position is the new value
    def move_max_y (self, value):
        self.min_y = value - self.get_maxheight()
    
    def move_max_x (self, value):
        self.min_x = value - self.get_maxwidth()
        
    def move_mid_y (self, value):
        self.min_y = value - (self.get_maxheight()/2)
    
    def move_mid_x (self, value):
        self.min_x = value - (self.get_maxwidth()/2)
    
    # max distance x
    def get_maxwidth (self):
        polygon = Polygon(self.points)
        return polygon.bounds[2] - polygon.bounds[0]
    
    def get_maxheight (self):
        polygon = Polygon(self.points)
        return polygon.bounds[3] - polygon.bounds[1]

    # Returns points (exlusion area) after applying min_x, min_y
    def get_points(self):
        return_points = []
        for point in self.points:
            return_points.append((self.min_x+point[0], self.min_y+point[1]))
        return return_points
        
    def move_rel(self, pos):
        # Store current position in history
        self.history.append(["move", [self.min_x, self.min_y]])
        #print (f'Current {self.min_x}, {self.min_y}')
        self.min_x += pos[0]
        self.min_y += pos[1]
        #print (f'New {self.min_x}, {self.min_y}')
        self.update_pos()
        
    def get_entry(self):
        return ((self.type, self.template, (self.min_x, self.min_y), self.points, self.cuts_as_list(), self.etches_as_list(), self.outers_as_list()))
        
    # returns the cuts as basic list of objects - eg. in same format as used by constructor
    # Cut type (eg. rect) followed by list containing strings or values (must work with eval string after subsitution)
    # "rect" [x, y, width, height]
    def cuts_as_list(self):
        cut_list = []
        for this_cut in self.cuts:
            cut_list.append(this_cut.unformat())
        return cut_list
    
    def etches_as_list(self):
        etch_list = []
        for this_etch in self.etches:
            etch_list.append(this_etch.unformat())
        return etch_list
    
    def outers_as_list(self):
        outer_list = []
        for this_outer in self.outers:
            outer_list.append(this_outer.unformat())
        return outer_list
        
    # if changing start then need to update cuts so use setters
    def set_start(self, start):
        self.history.append(["move", [self.min_x, self.min_y]])
        self.min_x = start[0]
        self.min_y = start[1]
        self.update_pos()
        
    # If start changes then update cuts and etches
    def update_pos(self):
        # Also set all cuts to new start
        for cut in self.cuts:
            cut.set_internal_offset((self.min_x, self.min_y))
        for etch in self.etches:
            etch.set_internal_offset((self.min_x, self.min_y))
        for outer in self.outers:
            outer.set_internal_offset((self.min_x, self.min_y))

    
    def get_exclude (self):
        return ExcludePolygon(self.get_points())
        
    # Creates cuts based around simple rectangle.
    # cut out for the entire window / door etc. no sills eg. shed window
    def set_cuts_rect(self):
        self.cuts.append (CutRect(self.start_pos, self.size))
    
    # Get all the cuts
    # First add the offset of the x,y position of the feature
    def get_cuts(self):
        return self.cuts
    
    def get_etches(self):
        return self.etches
    
    def get_outers(self):
        return self.outers
    
    def get_outers_cuts(self):
        cuts = []
        for outer in self.outers:
            cuts.append(outer.get_cut())
        return cuts
    
    def get_outers_etches(self):
        etches = []
        for outer in self.outers:
            etches.append(outer.get_etch())
        return etches
        
