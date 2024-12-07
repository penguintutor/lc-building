# Implements the same as SVGOut - but to the scene
# pass it the name of the scene and then call the functions to add the various parts (wall cuts / etches etc.)
# Typically these are walls, but could also be used for other "features" that are not walls

# Uses laser module and all classes (eg. cuts)
from laser import *
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsItem

# Settings is from gconfig
# Each objectview is a wall (or similar)
# Create as an object group and move items into it
class ObjView():
    def __init__ (self, scene, settings, coords = [0,0]):
        self.settings = settings
        self.scene = scene
        # Item Group (create later after creating first cut)
        #self.item_group = None
        self.item_group = self.scene.createItemGroup([])
        self.item_group.setFlag(QGraphicsItem.ItemIsMovable)
        self.item_group.setFlag(QGraphicsItem.ItemIsSelectable)
        self.offset = coords
        #print (f"Offset {self.offset}")
        
        #print (f"Obj view item is {self}")
        #print (f"Item group is {self.item_group}")
        
                
    def set_offset(self, offset):
        self.offset = offset

    # To prevent repetition then cuts, edges and outers are split into 2 types
    # standard_object = treat as a line / cut
    # polygon_object = convert to polygon
    def add_cut(self, cut):
        self.add_standard_object (cut, "cut")
        
    def add_outer(self, outer):
        self.add_standard_object (outer, "outer")

    # Generic version of add_cut, add_edge, add_outer
    # Pen is the pen type to use "cut", "outer", "etch"
    # If etch is used then optional parameter strength chooses appropriate etch strength
    def add_standard_object (self, object, pen, strength=5):
        # Get pen from gconfig
        if pen == "outer":
            pen_obj = self.settings.pen_outer
            # Special case is etch which also looks at strength
        elif pen == "etch":
            pen_obj = self.settings.pen_etch[strength]
            # Default is a cut
        else:
            pen_obj = self.settings.pen_cut
        if (object.get_type() == "line"):
            # get as pixels with offset added
            start_line = object.get_start_pixels_screen(self.offset)
            end_line = object.get_end_pixels_screen(self.offset)
            #print (f"     Start line {start_line},  End line {end_line}")
            this_object = self.scene.addLine(*start_line, *end_line, pen_obj) 
        elif (object.get_type() == "rect"):
            start_rect = object.get_start_pixels_screen(self.offset)
            rect_size = object.get_size_pixels_screen()
            this_object = self.scene.addRect(*start_rect, *rect_size, pen_obj) 
            #print (f"Rect points {start_rect} size {rect_size}")
        elif (object.get_type() == "polygon"):
            new_points = object.get_points_pixels_screen(self.offset)
            polygon = QPolygonF()
            for point in new_points:
                polygon.append(QPointF(*point))
            this_object = self.scene.addPolygon(polygon, pen_obj) 
            #print (f"Polygon points {polygon}")
        self.item_group.addToGroup(this_object)

        
    # Etch is treated as a special case where type is line and want to convert to polygon
    # Otherwise treat as any other object - but include strength
    # May need to change to a special gconfig setting in future
    def add_etch(self, etch):
        # Get strength from the etch object
        strength = etch.get_strength()
        pen_obj = self.settings.pen_etch[strength]
        # Special case for line etch as software tools not allow, plus need to add width
        if (etch.get_type() == "line" and self.settings.view_etch_as_polygon == True):
            # Check if etch_as_polygon set (in which case get polygon instead of line)
            # Really intended for actual output (eg. because laser cutter requires polygon)
            # May want to have different setting / pen size for display to screen
            new_points = etch.get_polygon_pixels_screen(self.offset)
            polygon = QPolygonF()
            for point in new_points:
                polygon.append(QPointF(*point))
            this_etch = self.scene.addPolygon(polygon, pen_obj) 
            self.item_group.addToGroup(this_etch)
        else:
           self.add_standard_object (etch, "etch", strength) 



