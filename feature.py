# A feature is always something that is part of a wall - eg. a door or a window
# Or a roof (which is treated as a type of wall)
# Different to an "extra" which is cut separately (eg. decoration that is mounted afterwards)
from laser import *

# Features must NOT overlap - unpredictable results in textures if do
class Feature():
    # x, y is top left
    # max is bottom right - forms rectangle to exclude
    def __init__ (self, min_x, min_y, max_x, max_y, cuts=None, etches=None):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        if cuts == None:
            self.cuts = []
        else:
            self.cuts = cuts
        if etches == None:
            self.etches = []
        else:
            self.etches = etches
        
    # Get area to exclude
    def get_area (self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)
        
    # Creates cuts based around simple rectangle.
    # cut out for the entire window no sills eg. shed window
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
    def __init__ (self, start_pos, size, cuts=None, etches=None):
        self.start_pos = start_pos
        self.size = size
        super().__init__ (start_pos[0], start_pos[1], start_pos[0]+size[0], start_pos[1]+size[1], cuts, etches)
    

# Defaults to cuts = None
# Don't normally want to cutout door, unless planning to reconnect with a hinge
# If do want to cut out then cuts myay be just 3 sides no bottom as that's cut already (unless step etc.)
# Perhaps handle by having different templates - Door with cutout, vs Etch Door
#todo work on this
class Door(Feature):
    def __init__ (self, start_pos, size, cuts=None, etches=None):
        self.start_pos = start_pos
        self.size = size
        super().__init__ (start_pos[0], start_pos[1], start_pos[0]+size[0], start_pos[1]+size[1], cuts, etches)
        
