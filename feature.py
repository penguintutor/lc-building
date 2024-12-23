# A feature is always something that is part of a wall - eg. a door or a window
# Or a roof (which is treated as a type of wall)
# Different to an "extra" which is cut separately (eg. decoration that is mounted afterwards)
from laser import *
from laserfactory import *

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
            #print (f"Creating cut {cut[0]} , {cut[1]}")
            self.cuts.append(Feature.lf.create_cut(cut[0], cut[1], (self.min_x, self.min_y)))
        # Do the same for etches
        self.etches = []
        for etch in etches:
            if etch == []:
                break
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
            self.outers.append(Feature.lf.create_outer(outer[0], outer[1], (self.min_x, self.min_y)))
        
        
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
    # Get area to exclude
    #def get_area (self):
    #    return (self.min_x, self.min_y, self.max_x, self.max_y)
    
    def get_exclude (self):
        return self.get_points()
        
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
        
