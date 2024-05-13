# A feature is always something that is part of a wall - eg. a door or a window
# Or a roof (which is treated as a type of wall)
# Different to an "extra" which is cut separately (eg. decoration that is mounted afterwards)
class Feature():
    # x, y is top left
    # max is bottom right - forms rectangle to exclude
    def __init__ (self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        
# Start pos is top left
# Size is (width, height)
# Size is of full window including any sills / border
# If cuts = None then will cut out a rectangle for the entire window no sills
# (eg. shed etc.) For frames etc. then provide list of lines in cuts which
# are as tuples, (startx, starty, endx, endy) - only lines allowed
# If use lines then must cut external lines as well, rectangle won't be cut
class Window(Feature):
    def __init__ (self, start_pos, size, cuts=None):
        self.start_pos = start_pos
        self.size = size
        self.cuts = None
        super().__init__ (start_pos[0], start_pos[1], start_pos[0]+size[0], start_pos[1]+size[1])
        
    def get_cuts(self):
        return_cuts = []
        if self.cuts == None:
            # Return rectangle based on start_pos and size
            return_cuts.append (("rect", self.start_pos, self.size))
        else:
            # Return list of cuts
            for cut in cuts:
                return_cuts.append(("line", (cut[0], cut[1]), (cut[2], cut[3])))
        return return_cuts