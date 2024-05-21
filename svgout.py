import svgwrite
from laser import *

# Settings is a dict of different settings
class SVGOut():
    def __init__ (self, filename, settings):
        self.settings = settings
        self.filename = filename
        self.offset = [0, 0]
        self.dwg = svgwrite.Drawing(filename, profile='tiny', size=(str(settings["docsize"][0]),str(settings["docsize"][1])))
        
    def set_offset(self, offset):
        self.offset = offset
    
    def add_cut(self, cut):
        if (cut.get_type() == "line"):
            # get as pixels with offset added
            start_line = cut.get_start_pixels(self.offset)
            end_line = cut.get_end_pixels(self.offset)
            self.dwg.add(self.dwg.line(start_line, end_line, stroke=self.settings['cutstroke'], stroke_width=self.settings['strokewidth']))
        elif (cut.get_type() == "rect"):
            start_rect = cut.get_start_pixels(self.offset)
            rect_size = cut.get_size_pixels()
            self.dwg.add(self.dwg.rect(start_rect, rect_size, stroke=self.settings['cutstroke'], fill="none", stroke_width=self.settings['strokewidth']))
        
    def add_etch(self, etch):
        # Special case for line etch as software tools not allow, plus need to add width
        if (etch.get_type() == "line"):
            # Check if etch_as_polygon set (in which case get polygon instead of line)
            if self.settings['etchaspolygon'] == True:
                new_points = etch.get_polygon_pixels(self.offset)
                self.dwg.add(self.dwg.polygon(new_points, stroke=self.settings['etchstroke'], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
            # Otherwise treat as line
            else:
                # start_etch is modified start
                start_line = etch.get_start_pixels(self.offset)
                end_line = etch.get_end_pixels(self.offset)
                self.dwg.add(self.dwg.line(start_line, end_line, stroke=self.settings['etchstroke'], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
        elif (etch.get_type() == "rect"):
            start_rect = etch.get_start_pixels(self.offset)
            rect_size = etch.get_size_pixels()
            self.dwg.add(self.dwg.rect(start_rect, rect_size, stroke=self.settings['etchstroke'], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))
        elif (etch.get_type() == "polygon"):
            new_points = etch.get_points_pixels(self.offset)
            self.dwg.add(self.dwg.polygon(new_points, stroke=self.settings['etchstroke'], fill=self.settings['etchfill'], stroke_width=self.settings['strokewidth']))

    def save(self):
        self.dwg.save()