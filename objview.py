# Implements the same as SVGOut - but to the scene
# pass it the name of the scene and then call the functions to add the various parts (wall cuts / etches etc.)
# Typically these are walls, but could also be used for other "features" that are not walls

# Uses laser module and all classes (eg. cuts)
from laser import *
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF

# Settings is a dict of different settings
class ObjView():
    def __init__ (self, scene, settings, coords = [0,0]):
        self.settings = settings
        self.scene = scene
        self.offset = coords
        #self.dwg = svgwrite.Drawing(filename, profile='tiny', size=(str(settings["docsize"][0]),str(settings["docsize"][1])))
        
    def set_offset(self, offset):
        self.offset = offset
    
    def add_cut(self, cut):
        if (cut.get_type() == "line"):
            # get as pixels with offset added
            start_line = cut.get_start_pixels_screen(self.offset)
            end_line = cut.get_end_pixels_screen(self.offset)
            #print (f"     Start line {start_line},  End line {end_line}")
            self.scene.addLine(*start_line, *end_line) #, stroke=self.settings['cutstroke'], stroke_width=self.settings['strokewidth'])
        elif (cut.get_type() == "rect"):
            start_rect = cut.get_start_pixels_screen(self.offset)
            rect_size = cut.get_size_pixels_screen()
            self.scene.addRect(*start_rect, *rect_size) # , stroke=self.settings['cutstroke'], fill="none", stroke_width=self.settings['strokewidth']))
        elif (cut.get_type() == "polygon"):
            new_points = cut.get_points_pixels_screen(self.offset)
            polygon = QPolygonF()
            for point in new_points:
                polygon.append(QPointF(*point))
            self.scene.addPolygon(polygon) #, stroke=self.settings['cutstroke'], fill="none", stroke_width=self.settings['strokewidth']))
        
    def add_etch(self, etch):
        # Get strength from the etch object
        strength = etch.get_strength()
        # Special case for line etch as software tools not allow, plus need to add width
        if (etch.get_type() == "line"):
            # Check if etch_as_polygon set (in which case get polygon instead of line)
            # Really intended for actual output (eg. because laser cutter requires polygon)
            # May want to have different setting / pen size for display to screen
            if self.settings.etch_as_polygon == True:
                new_points = etch.get_polygon_pixels_screen(self.offset)
                polygon = QPolygonF()
                for point in new_points:
                    polygon.append(QPointF(*point))
                self.scene.addPolygon(polygon) # , stroke=self.settings['etchstrokes'][strength], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
            # Otherwise treat as line
            else:
                # start_etch is modified start
                start_line = etch.get_start_pixels_screen(self.offset)
                end_line = etch.get_end_pixels_screen(self.offset)
                self.scene.addLine(*start_line, *end_line) #, stroke=self.settings['etchstrokes'][strength], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
        elif (etch.get_type() == "rect"):
            start_rect = etch.get_start_pixels_screen(self.offset)
            rect_size = etch.get_size_pixels_screen()
            self.scene.addRect(*start_rect, *rect_size)
            #, stroke=self.settings['etchstrokes'][strength], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
        elif (etch.get_type() == "polygon"):
            new_points = etch.get_points_pixels_screen(self.offset)
            polygon = QPolygonF()
            for point in new_points:
                polygon.append(QPointF(*point))
            self.scene.addPolygon(polygon) #, stroke=self.settings['etchstrokes'][strength], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
