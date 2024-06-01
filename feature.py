# A feature is always something that is part of a wall - eg. a door or a window
# Or a roof (which is treated as a type of wall)
# Different to an "extra" which is cut separately (eg. decoration that is mounted afterwards)
from laser import *
from laserfactory import *

# Each cut is defined in templates (and building data)
# Cut type (eg. rect) followed by list containing strings or values (must work with eval string after subsitution)
# "rect" [x, y, width, height]
# Features must NOT overlap - unpredictable results in textures if do
class Feature():
    lf = LaserFactory()
    # x, y is top left
    # max is bottom right - forms rectangle to exclude
    def __init__ (self, startpos, size, cuts=[], etches=[], outers=[]):
        self.min_x = startpos[0]
        self.min_y = startpos[1]
        self.max_x = startpos[0]+size[0]
        self.max_y = startpos[1]+size[1]
        # Cuts needs to be converted into laser cut objects
        self.cuts = []
        for cut in cuts:
            if cut == []:
                break
            self.cuts.append(Feature.lf.create_cut(cut[0], cut[1], (self.min_x, self.min_y)))
        # Do the same for etches
        self.etches = []
        for etch in etches:
            if etch == []:
                break
            self.etches.append(Feature.lf.create_etch(etch[0], etch[1], (self.min_x, self.min_y)))
        self.outers = []
        for outer in outers:
            if outer == []:
                break
            self.outers.append(Feature.lf.create_outer(outer[0], outer[1], (self.min_x, self.min_y)))
        
            
        
    # if changing start then need to update cuts so use setters
    def set_start(self, start):
        self.min_x = start[0]
        self.min_y = start[1]
        self.update_pos()
        
    # If start changes then update cuts and etches
    def update_pos(self):
        # Also set all cuts to new start
        for cut in cuts:
            cut.set_internal_offset((self.min_x, self.min_y))
        
    # Get area to exclude
    def get_area (self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)
        
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
        
