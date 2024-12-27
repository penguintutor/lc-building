# Class to handle laser objects
# These are cuts or etches
# Typically cuts will be lines which cut fully through the material
# whereas etches are shapes (rect / polygons)

# Child classes are created for both Cut and Etch to make it easier
# to create

# all dimensions are in mm (convert using scale if required)

# internal_offset if used is for relative to wall
# eg position of top left of feature

# Standard methods uses scale class for scaling
# Methods with _screen return using vs (zoom level)

from scale import Scale
from viewscale import ViewScale

class Laser():
    # Scale convertor set as a class variable
    # Set once during app startup and then can use for all subclasses
    # Alternative to setting up a singleton
    sc = None
    # Also has view scale
    vs = ViewScale()
    
    def __init__(self, type, internal_offset):
        self.type = type
        self.io = internal_offset
        
    def get_type(self):
        return self.type
    
    # Call this once to pass the scale object
    def set_scale_object(self, sc):
        Laser.sc = sc
        
    def set_internal_offset(self, internal_offset):
        self.io = internal_offset
        
    # If want to change scale use this - not the set_scale_object
    # Provide as the scale name (eg. OO)
    # Returns scale if success or None
    def set_scale(self, scale):
        return self.sc.set_scale(scale)
    

class Cut(Laser):
    def __init__(self, type, internal_offset):
        super().__init__(type, internal_offset)
        
       
# Start and end are tuples

class CutLine(Cut):
    def __init__(self, start, end, internal_offset=(0,0)):
        self.start = start
        self.end = end
        super().__init__("line", internal_offset)
        
    # unformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("line", (self.start, self.end)))


    def __str__(self):
        return f'Cut {self.type} from {self.start} to {self.end} io {self.io}'
    
    # Get start value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_start_pixels(self, offset=(0,0)):
        # Add internal offset to offset
        start_io = (self.start[0]+self.io[0], self.start[1]+self.io[1])
        start_pixels = Laser.sc.convert(start_io)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    def get_start_pixels_screen(self, offset=(0,0)):
        # Add internal offset to offset
        start_io = (self.start[0]+self.io[0], self.start[1]+self.io[1])
        start_pixels = Laser.vs.convert(start_io)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Get end value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_end_pixels(self, offset=(0,0)):
        end_io = (self.end[0]+self.io[0], self.end[1]+self.io[1])
        end_pixels = Laser.sc.convert(end_io)
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])
    
    def get_end_pixels_screen(self, offset=(0,0)):
        end_io = (self.end[0]+self.io[0], self.end[1]+self.io[1])
        end_pixels = Laser.vs.convert(end_io)
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])

class CutRect(Cut):
    def __init__(self, start, size, internal_offset=(0,0)):
        self.start = start
        self.size = size
        super().__init__("rect", internal_offset)
        
    # uformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("rect", (self.start, self.size)))
        
    def __str__(self):
        return f'Cut {self.type} from {self.start} size {self.size} io {self.io}'
          
    def get_start_pixels(self, offset=(0,0)):
        start_io = ([self.start[0]+self.io[0], self.start[1]+self.io[1]])
        start_pixels = Laser.sc.convert(start_io)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    def get_start_pixels_screen(self, offset=(0,0)):
        start_io = ([self.start[0]+self.io[0], self.start[1]+self.io[1]])
        start_pixels = Laser.vs.convert(start_io)
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Note that size does not need offset
    def get_size_pixels(self):
        return Laser.sc.convert(self.size)
    
    def get_size_pixels_screen(self):
        return Laser.vs.convert(self.size)
    
class CutPolygon(Cut):
    def __init__(self, points, internal_offset=(0,0)):
        self.points = points
        super().__init__("polygon", internal_offset)
        
    # unformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("polygon", self.points))
        
    # Add internal offset to points
    def get_points(self):
        new_points = []
        for point in self.points:
            new_points.append((point[0]+self.io[0], point[1]+self.io[1]))
        return new_points
    
    # Offset is applied to all points
    def get_points_pixels(self, offset=(0,0)):
        new_points = []
        for point in self.points:
            sc_point = Laser.sc.convert((point[0]+self.io[0], point[1]+self.io[1]))
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points
    
    def get_points_pixels_screen(self, offset=(0,0)):
        new_points = []
        for point in self.points:
            sc_point = Laser.vs.convert((point[0]+self.io[0], point[1]+self.io[1]))
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points

# type could be "line" / "rect" etc. 
class Etch(Laser):
    def __init__(self, type, internal_offset):
        super().__init__(type, internal_offset)
        
    def get_strength(self):
        return self.strength
        
        
# Start and end are tuples
class EtchLine(Etch):
    # Default etch width if none others set on individual class
    # Used by etch lines only, but can be accessed by all instances
    global_etch_width = 10
    def __init__(self, start, end, internal_offset=(0,0), strength=5, etch_width=None):
        self.strength = strength
        self.start = start
        self.end = end
        # how wide to cut (cannot have line as lightburn doesn't like it)
        # If set to None (default) then look at class variable global_etch_width
        self.etch_width = etch_width
        super().__init__("line", internal_offset)
    
    # unformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("line", (self.start, self.end)))
    
    def __str__(self):
        return f'Etch {self.type} from {self.start} to {self.end} io {self.io}'
        
    def get_start(self):
        return (self.start[0]+self.io[0], self.start[1]+self.io[1])
    
    # Get start value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_start_pixels(self, offset=(0,0)):
        # Add internal offset to offset
        start_pixels = self.sc.convert(self.get_start())
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    def get_start_pixels_screen(self, offset=(0,0)):
        # Add internal offset to offset
        start_pixels = self.vs.convert(self.get_start())
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Get end value converted by scale and into pixels
    # If supplied offset is in pixels relative to start of object
    def get_end_pixels(self, offset=(0,0)):
        end_pixels = self.sc.convert(self.get_end())
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])
    
    def get_end_pixels_screen(self, offset=(0,0)):
        end_pixels = self.vs.convert(self.get_end())
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])
    
    def get_end(self):
        return (self.end[0]+self.io[0], self.end[1]+self.io[1])
    
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
            point_io = (point[0]+self.io[0], point[1]+self.io[1])
            sc_point = Laser.sc.convert(point_io)
            new_points.append(((offset[0]+sc_point[0]),(offset[1]+sc_point[1])))
        return new_points
        
    def get_polygon_pixels_screen(self, offset=(0,0)):
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
            point_io = (point[0]+self.io[0], point[1]+self.io[1])
            sc_point = Laser.vs.convert(point_io)
            new_points.append(((offset[0]+sc_point[0]),(offset[1]+sc_point[1])))
        return new_points
        
        
class EtchRect(Etch):
    def __init__(self, start, size, internal_offset=(0,0), strength=5):
        self.strength = strength
        self.start = start
        self.size = size
        super().__init__("rect", internal_offset)
    
    # uformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("rect", (self.start, self.size)))
    
    def get_start(self):
        return (self.start[0]+self.io[0], self.start[1]+self.io[1])
    
    def get_size(self):
        return self.size
    
    def get_start_pixels(self, offset=(0,0)):
        start_pixels = Laser.sc.convert(self.get_start())
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    def get_start_pixels_screen(self, offset=(0,0)):
        start_pixels = Laser.vs.convert(self.get_start())
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    # Note that size does not need offset
    def get_size_pixels(self):
        return Laser.sc.convert(self.size)
    
    def get_size_pixels_screen(self):
        return Laser.vs.convert(self.size)
        
class EtchPolygon(Etch):
    def __init__(self, points, internal_offset=(0,0), strength=5):
        self.strength = strength
        self.points = points
        super().__init__("polygon", internal_offset)
        
    # unformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("polygon", self.points))
        
    def get_points(self):
        new_points = []
        for point in self.points:
            new_points.append((point[0]+self.io[0], point[1]+self.io[1]))
        return new_points
    
    def get_points_offset(self, offset):
        new_points = []
        for point in self.get_points():
            new_points.append([(offset[0]+point[0]),(offset[1]+point[1])])
        return new_points
    
    # Offset is applied to all points
    def get_points_pixels(self, offset=(0,0)):
        new_points = []
        for point in self.get_points():
            sc_point = Laser.sc.convert(point)
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points

    def get_points_pixels_screen(self, offset=(0,0)):
        new_points = []
        for point in self.get_points():
            sc_point = Laser.vs.convert(point)
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points


# Outer can be either cut or edge
# Determined when generating, so convert to appropriate type when required
# Outer must have a get_args method that allows creation of cut / edge
# TODO - If etch current default to 5, need to make configurable
class Outer(Laser):
    def __init__(self, type, internal_offset):
        super().__init__(type, internal_offset)
        
    # Unable to use laserfactory due to circular imports
    # implement get_cut / get_etch in each of the child classes
class OuterLine(Outer):
    def __init__(self, start, end, internal_offset=(0,0), strength=5):
        self.strength = strength
        self.start = start
        self.end = end
        super().__init__("line", internal_offset)
        
    # unformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("line", (self.start, self.end)))
        
    def get_args(self):
        return [self.start, self.end]
    
    def get_start(self):
        return (self.start[0]+self.io[0], self.start[1]+self.io[1])
    
    def get_end(self):
        return (self.end[0]+self.io[0], self.end[1]+self.io[1])

    def get_size(self):
        return self.size

    # Returns as a cut object
    def get_cut(self):
        args = self.get_args()
        return CutLine(args[0], args[1], self.io)
    
    def get_etch(self):
        args = self.get_args()
        return EtchLine(args[0], args[1], self.io, strength)
    
    def get_start_pixels_screen(self, offset=(0,0)):
        # Add internal offset to offset
        start_pixels = self.vs.convert(self.get_start())
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    def get_end_pixels_screen(self, offset=(0,0)):
        end_pixels = self.vs.convert(self.get_end())
        # Add offset
        return ([end_pixels[0]+offset[0], end_pixels[1]+offset[1]])
    
class OuterRect(Outer):
    def __init__(self, start, size, internal_offset=(0,0), strength=5):
        self.strength = strength
        self.start = start
        self.size = size
        super().__init__("rect", internal_offset)
        
    # uformat returns (type, [list_of_values]) 
    def unformat(self):
       return (("rect", (self.start, self.size))) 
        
    def get_args(self):
        return [self.start, self.size]
    
    # Returns as a cut object
    def get_cut(self):
        args = self.get_args()
        return CutRect(args[0], args[1], self.io)
    
    def get_etch(self):
        args = self.get_args()
        return EtchRect(args[0], args[1], self.io)

    def get_start_pixels_screen(self, offset=(0,0)):
        start_pixels = Laser.vs.convert(self.get_start())
        # Add offset
        return ([start_pixels[0]+offset[0], start_pixels[1]+offset[1]])
    
    
    def get_size_pixels_screen(self):
        return Laser.vs.convert(self.size)
    
class OuterPolygon(Outer):
    def __init__(self, points, internal_offset=(0,0), strength=5):
        self.strength = strength
        self.points = points
        super().__init__("polygon", internal_offset)
        
    # unformat returns (type, [list_of_values]) 
    def unformat(self):
        return (("polygon", self.points))
        
    def get_args(self):
        return self.points

    # Returns as a cut object
    def get_cut(self):
        return CutPolygon(self.get_args(), self.io)
    
    def get_etch(self):
        return EtchPolygon(self.get_args(), self.io)

    def get_points_pixels_screen(self, offset=(0,0)):
        new_points = []
        for point in self.get_points():
            sc_point = Laser.vs.convert(point)
            new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
        return new_points
