# Implements the same as SVGOut - but to the scene
# pass it the name of the scene and then call the functions to add the various parts (wall cuts / etches etc.)
# Typically these are walls, but could also be used for other "features" that are not walls

# Uses laser module and all classes (eg. cuts)
from laser import *
from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QPolygonF, QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsItem
from objgroup import ObjGroup

# Settings is from gconfig
# Each objectview is a wall (or similar)
# type is optional can be used to distinguish between objects
# eg. so can re-render the texture without effecting other objects
# Create as an object group and move items into it
class ObjView():
    def __init__ (self, scene, settings, coords = (0,0), type="unknown", moveable=True):
        #print ("Adding objview to scene {scene}")
        #print (f"Creating object moveable {moveable}")
        self.settings = settings  # also known as gconfig
        self.scene = scene
        self.type = type
        # Item Group (create later after creating first cut)
        #self.item_group = None
        #self.item_group = self.scene.createItemGroup([])
        self.item_group = ObjGroup(self.settings)
        self.scene.addItem(self.item_group)
        #self.item_group.addToGroup()
        # If wall edit then wall is not selectable or moveable
        if moveable:
            self.item_group.setFlag(QGraphicsItem.ItemIsMovable)
            self.item_group.setFlag(QGraphicsItem.ItemIsSelectable)
            self.item_group.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.offset = coords
        # Test override offset - instead use graphicsscene to manage position
        self.offset = (0,0)
        # Save the current position
        pos_point = self.item_group.pos().toPoint()
        self.pos = [pos_point.x(), pos_point.y()]
        # Update new_pos when moved
        #self.new_pos = (0,0)
        # Use min and max to track size of the group
        self.x_min = 0
        self.y_min = 0
        self.x_max = 0
        self.y_max = 0

    # return minx, miny, maxx, maxy
    def get_bounding (self):
        return [
            self.pos[0] + self.x_min,
            self.pos[1] + self.y_min,
            self.pos[0] + self.x_max,
            self.pos[1] + self.y_max
            ]

    def get_width(self):
        return self.x_max - self.x_min
    
    def get_height(self):
        return self.y_max - self.y_min
    
    def get_size (self):
        return [self.get_width(), self.get_height()]
        
        
    # Check if moved - and update position if moved 
    def has_moved(self):
        new_pos_point = self.item_group.pos().toPoint()
        new_pos = [new_pos_point.x(), new_pos_point.y()]
        if new_pos != self.pos:
            self.pos = new_pos
            return True
        return False
        
    def set_pos(self, pos):
        self.pos = pos
        self.item_group.setPos(QPoint(*pos))
        
    def get_pos(self):
        # Perhaps regenerate at this point??
        return self.pos
                
    def set_offset(self, offset):
        self.offset = offset
        
    def itemChange(self, change, value):
        print (f"Item change {change}, {value}")

    # To prevent repetition then cuts, edges and outers are split into 2 types
    # standard_object = treat as a line / cut
    # polygon_object = convert to polygon
    def add_cut(self, cut):
        self.add_standard_object (cut, "cut")
        
    def add_outer(self, outer):
        self.add_standard_object (outer, "outer")
        
    # Should only be used for editview
    # Draw polygon for background of features
    def add_exclude(self, exclude):
        self.add_standard_object (exclude, "exclude")
        
    def _upd_x_size (self, xval):
        if xval < self.x_min:
            self.x_min = xval
        if xval > self.x_max:
            self.x_max = xval
            
    def _upd_y_size (self, yval):
        if yval < self.y_min:
            self.y_min = yval
        if yval > self.y_max:
            self.y_max = yval

    # Generic version of add_cut, add_edge, add_outer
    # Pen is the pen type to use "cut", "outer", "etch"
    # If etch is used then optional parameter strength chooses appropriate etch strength
    def add_standard_object (self, object, pen, strength=5):
        # Default is no fill - only applied to polygon
        brush_obj = QBrush()
        # Get pen from gconfig
        if pen == "outer":
            pen_obj = self.settings.pen_outer
            # Special case is etch which also looks at strength
        elif pen == "etch":
            pen_obj = self.settings.pen_etch[strength]
            # Default is a cut
        elif pen == "exclude":
            # Not from settings - this is fill for background of features
            # Set to white
            pen_obj = QPen(QColor(255,255,255))
            brush_obj = QBrush(QColor(255,255,255))
        else:
            pen_obj = self.settings.pen_cut
        if (object.get_type() == "line"):
            # get as pixels with offset added
            start_line = object.get_start_pixels_screen(self.offset)
            end_line = object.get_end_pixels_screen(self.offset)
            self._upd_x_size(start_line[0])
            self._upd_x_size(end_line[0])
            self._upd_y_size(start_line[1])
            self._upd_y_size(end_line[1])
            #print (f"     Start line {start_line},  End line {end_line}")
            this_object = self.scene.addLine(*start_line, *end_line, pen_obj) 
        elif (object.get_type() == "rect"):
            start_rect = object.get_start_pixels_screen(self.offset)
            rect_size = object.get_size_pixels_screen()
            this_object = self.scene.addRect(*start_rect, *rect_size, pen_obj)
            self._upd_x_size(start_rect[0])
            self._upd_x_size(start_rect[0]+rect_size[0])
            self._upd_y_size(start_rect[1])
            self._upd_y_size(start_rect[1]+rect_size[1])
            #print (f"Rect points {start_rect} size {rect_size}")
        elif (object.get_type() == "polygon"):
            new_points = object.get_points_pixels_screen(self.offset)
            polygon = QPolygonF()
            for point in new_points:
                polygon.append(QPointF(*point))
            this_object = self.scene.addPolygon(polygon, pen_obj, brush_obj) 
            #print (f"Polygon points {polygon}")
        self.item_group.addToGroup(this_object)
        #print ("Standard object added {self.pos}")

        
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


