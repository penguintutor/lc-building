# A feature is always something that is part of a wall - eg. a door or a window
# Or a roof (which is treated as a type of wall)
# Different to an "extra" which is cut separately (eg. decoration that is mounted afterwards)
from laser import *

# Each cut is defined in templates (and building data)
# Cut type (eg. rect) followed by list containing strings or values (must work with eval string after subsitution)
# "rect" [x, y, width, height]
# Features must NOT overlap - unpredictable results in textures if do
class Feature():
    # x, y is top left
    # max is bottom right - forms rectangle to exclude
    def __init__ (self, min_x, min_y, max_x, max_y, cuts=[], etches=[]):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.cuts = cuts
        self.etches = etches
        
    # Get area to exclude
    def get_area (self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)
        
    # Creates cuts based around simple rectangle.
    # cut out for the entire window / door etc. no sills eg. shed window
    def set_cuts_rect(self):
        self.cuts.append (CutRect(self.start_pos, self.size))
    
    def get_cuts(self):
        return self.cuts
    
    def get_etches(self):
        return self.etches
        
# Start pos is top left
# Size is (width, height)
# Size is of full window including any sills / border
# If cuts = None then cutout nothing - but can be added by set_cuts_rect
# For frames etc. then provide list of lines in cuts which
# are as tuples, (startx, starty, endx, endy) - only lines allowed
# If use lines then must cut external lines as well, rectangle won't be cut
class Window(Feature):
    def __init__ (self, start_pos, size, cuts=[], etches=[]):
        self.start_pos = start_pos
        self.size = size
        super().__init__ (start_pos[0], start_pos[1], start_pos[0]+size[0], start_pos[1]+size[1], cuts, etches)
    

# Defaults to cuts = None
# Don't normally want to cutout door, unless planning to reconnect with a hinge (eg. larger scales)
# If do want to cut out then cuts may be just 3 sides no bottom as that's cut already (unless step etc.)
# Perhaps handle by having different templates - Door with cutout, vs Etch Door
class Door(Feature):
    def __init__ (self, start_pos, size, cuts=[], etches=[]):
        self.start_pos = start_pos
        self.size = size
        super().__init__ (start_pos[0], start_pos[1], start_pos[0]+size[0], start_pos[1]+size[1], cuts, etches)
        
