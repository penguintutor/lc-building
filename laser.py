# Class to handle laser objects
# These are cuts or etches
# Typically cuts will be lines which cut fully through the material
# whereas etches are shapes (rect / polygons)

# Subclasses are created for both Cut and Etch to make it easier
# to create

# all dimensions are in mm (convert using scale if required)
class Laser():
    def __init__(self, type, values):
        self.type = type
        self.values = values
        
    def get_type(self):
        return self.type
        

class Cut(Laser):
    def __init__(self, type, values):
        super().__init__(type, values)
        
    # Returns as appropriate format for using in svg write
    # Even though subclassed we use a single get_cut which handles
    # All different subclasses in a uniform way
    # Note returns a tuple, but different depending upon the shape
    # eg. line is start and end, rect is start and size and polygon is list of points
    def get_cut(self):
        if self.type == "line":
            return ("line", self.values[0], self.values[1])
        elif self.type == "rect":
            return ("rect", self.values[0], self.values[1])
        elif self.type == "polygon":
            return ("polygon", points)
        
        
# Start and end are tuples
class CutLine(Cut):
    def __init__(self, start, end):
        super().__init__("line", (start, end))
        
class CutRect(Cut):
    def __init__(self, start, size):
        super().__init__("rect", (start, size))

# type could be "line" / "rect" etc. 
class Etch(Laser):
    def __init__(self, type, values):
        super().__init__(type, values)
        
# Start and end are tuples
class EtchLine(Etch):
    # Default etch width if none others set on individual class
    # Used by etch lines only, but can be accessed by all instances
    global_etch_width = 10
    def __init__(self, start, end, etch_width=None):
        self.start = start
        self.end = end
        # how wide to cut (cannot have line as lightburn doesn't like it)
        # If set to None (default) then look at class variable global_etch_width
        self.etch_width = etch_width
        super().__init__("line", (start, end))
        
    def get_start(self):
        return self.start
    
    def get_end(self):
        return self.end
    
    def set_global_width(self, line_width):
        self.global_etch_width = line_width
        
class EtchRect(Etch):
    def __init__(self, start, size):
        self.start = start
        self.size = size
        super().__init__("rect", (start, size))
    
    def get_start(self):
        return self.start
    
    def get_size(self):
        return self.size
        
class EtchPolygon(Etch):
    def __init__(self, points):
        self.points = points
        super().__init__("polygon", (points))
        
    def get_points(self):
        return self.points