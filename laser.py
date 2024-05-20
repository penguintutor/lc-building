# Class to handle laser objects
# These are cuts or etches
# Typically cuts will be lines which cut fully through the material
# whereas etches are shapes (rect / polygons)

# Subclasses are created for both Cut and Etch to make it easier
# to create

# all dimensions are in mm (convert using scale if required)
class Laser():
    # Scale convertor set as a class variable
    # Set once during app startup and then can use for all subclasses
    # Alternative to setting up a singleton
    sc = None
    
    def __init__(self, type, values):
        self.type = type
        self.values = values
        
    def get_type(self):
        return self.type
    
    # Call this once to pass the scale object
    def set_scale_object(self, sc):
        Laser.sc = sc
        
    # If want to change scale use this - not the set_scale_object
    # Provide as the scale name (eg. OO)
    # Returns scale if success or None
    def set_scale(self, scale):
        return self.sc.set_scale(scale)
        

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
        self.start = start
        self.end = end
        super().__init__("line", (start, end))

    # Get start value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_start_pixels(self, offset=(0,0)):
        start_pixels = Laser.sc.convert(self.start)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Get end value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_end_pixels(self, offset=(0,0)):
        end_pixels = Laser.sc.convert(self.end)
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])

class CutRect(Cut):
    def __init__(self, start, size):
        self.start = start
        self.size = size
        super().__init__("rect", (start, size))
        
    def get_start_pixels(self, offset=(0,0)):
        start_pixels = Laser.sc.convert(self.start)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Note that size does not need offset
    def get_size_pixels(self):
        return Laser.sc.convert(self.size)
    
class CutPolygon(Cut):
    def __init__(self, points):
        self.points = points
        super().__init__("polygon", (points))
        
    def get_points(self):
        return self.points
    
    # Offset is applied to all points
    def get_points_pixels(self, offset=(0,0)):
        new_points = []
        for point in self.points:
            sc_point = Laser.sc.convert(point)
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points

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
    
    # Get start value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_start_pixels(self, offset=(0,0)):
        start_pixels = self.sc.convert(self.start)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Get end value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_end_pixels(self, offset=(0,0)):
        end_pixels = self.sc.convert(self.end)
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])
    
    def get_end(self):
        return self.end
    
    def set_global_width(self, line_width):
        EtchLine.global_etch_width = line_width
        
    # Gets a line as a polygon instead
    # Required for etches which don't allow lines
    def get_polygon_pixels(self, offset=(0,0)):
        # half the width - first check local (to this line) - otherwise default to global
        if self.etch_width != None:
            hw = self.etch_width / 2
        else:
            hw = EtchLine.global_etch_width / 2
        # Create an approxmation by only widening along thinest part (dx vs dy)
        # For a horizontal / vertical line this this is accurate
        # If not then it's an approximation
        # As this is for a laser cutter the approximation will not be noticed when etched
        # although may be able to see if using vector editor

        # Need to know which is min and max x determine if increase
        # or decrease appropriate values
        dx = abs(self.end[0] - self.start[0])
        dy = abs(self.end[1] - self.start[1])
        # If more vertical than horizontal
        if (dy > dx):
            points = [
                (self.start[0]-hw, self.start[1]),
                (self.start[0]+hw, self.start[1]),
                (self.end[0]+hw, self.end[1]),
                (self.end[0]-hw, self.end[1]),
                (self.start[0]-hw, self.start[1])
                ]
        # More horizontal than vertical
        else:
            points = [
                (self.start[0], self.start[1]-hw),
                (self.end[0], self.end[1]-hw),
                (self.end[0], self.end[1]+hw),
                (self.start[0], self.start[1]+hw),
                (self.start[0], self.start[1]-hw)
                ]
        # Now convert to scale and add offsets
        new_points = []
        for point in points:
            sc_point = Laser.sc.convert(point)
            new_points.append(((offset[0]+sc_point[0]),(offset[1]+sc_point[1])))
        return new_points
        
class EtchRect(Etch):
    def __init__(self, start, size):
        self.start = start
        self.size = size
        super().__init__("rect", (start, size))
    
    def get_start(self):
        return self.start
    
    def get_size(self):
        return self.size
    
    def get_start_pixels(self, offset=(0,0)):
        start_pixels = Laser.sc.convert(self.start)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Note that size does not need offset
    def get_size_pixels(self):
        return Laser.sc.convert(self.size)
        
class EtchPolygon(Etch):
    def __init__(self, points):
        self.points = points
        super().__init__("polygon", (points))
        
    def get_points(self):
        return self.points
    
    # Offset is applied to all points
    def get_points_pixels(self, offset=(0,0)):
        new_points = []
        for point in self.points:
            sc_point = Laser.sc.convert(point)
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points
