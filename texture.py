# Texture is an etch applied to a wall (or similar)
# Not shown where conflict with a feature (eg. window)
# Creates an instance for each element - then can use to detect
# if it needs to be removed because of other features
import copy
from laser import *
from helpers import *
from shapely import Point, Polygon, LineString

# Only work in mm
# Wall should handle conversion to pixels
# settings is dependent upon style - eg. brick_width only on bricks
# fullwall option is whether to automatically extend the points to the full wall
# in the event that the wall is changed this is default as GUI does not support partial textures
class Texture():
    def __init__ (self, points, style="", settings=None, fullwall=True):
        self.fullwall = fullwall
        self.points = copy.copy(points)
        self.style = style
        if settings != None: 
            # creates a copy of the settings in case settings list is reused upstream
            self.settings = copy.copy(settings)
        else:
            self.settings = {}
        # Convert points to a polygon
        self.polygon = Polygon(points)
        self.disable = False   # Allows to disable completely if not required
        self.excludes = []     # Excludes is replaced each time get_etches is called to ensure always updated
        
    # based on texture get suggested step size (eg. for brick this is height of brick + mortor
    def get_step_size(self):
        size = 150
        if self.style == "brick":
            size = self.settings["brick_etch"] + self.settings["brick_height"]
        elif self.style == "tile":
            size = self.settings["tile_etch"] + self.settings["tile_height"]
        elif self.style == "wood":
            size = self.settings["wood_etch"] + self.settings["wood_height"]
        return size
        
    # Change texture
    # Can just change texture style, or can also change all settings
    # old settings will not be retained
    # Most likely would change both settings and style
    def change_texture(self, style, settings=None):
        self.style = style
        if settings != None:
            # creates a copy of the settings in case settings list is reused upstream
            self.settings = copy.copy(settings)
            
    # Change the points to new 
    def change_points (self, points):
        self.points = copy.copy(points)
        self.polygon = Polygon(points)
        
    # Returns a setting value or "" if nt exist
    def get_setting_str (self, value):
        if value in self.settings.keys():
            return self.settings[value]
        else:
            return ""
            
    def get_entry(self):
        return ((self.points, self.style, self.settings))
            
    # Returns the texture as etches
    # excludes is a list of polygons for areas to exclude texture from
    # ie. Features - doors windows etc.
    def get_etches(self, excludes=[]):
        #print (f"Get etches - excluding {excludes}")
        # Update excludes so that this is applied across the texture
        self.excludes = excludes
        
        # Call appropriate texture generator based on style
        if self.style == "horizontal_wood" or self.style=="wood":
            return self._get_etches_horizontal_wood()
        elif self.style == "brick":
            return self._get_etches_bricks()
        elif self.style == "tile":
            return self._get_etches_tiles()
        else:
            return []
    
    
    # Returns horizontal etch lines representing a wood texture
    # Typically set width to 0 (full width of building)
    # With a wood_width then would go to that length before starting again
    # Does not stagger alternate lines
    def _get_etches_horizontal_wood(self):
        lines = []
        etches = []
        etch_width = self.settings["wood_etch"]
        wood_height = self.settings["wood_height"]
        if "wood_width" in self.settings:
            wood_width = self.settings["wood_width"]
        else:
            wood_width = 0
        min_x = self.polygon.bounds[0]+1
        max_x = self.polygon.bounds[2]-1
        min_y = self.polygon.bounds[1]+1
        max_y = self.polygon.bounds[3]-1
        min_wood_size = wood_height / 4
        # Generate horizontal lines across full width of wall
        # Starting bottom left
        current_y = self.polygon.bounds[3]-1
        while current_y > min_y:
            current_y -= (wood_height + etch_width)
            # If less than 1/4 wood size left then stop
            if current_y < min_y + min_wood_size:
                break
            lines.extend(self._line([min_x, current_y],[max_x, current_y]))
        # Ignore wood width if default (0)
        if wood_width > 0:
            # Apply vertical lines unless width is default (0)
            current_x = 0
            while current_x < max_x:
                current_x += wood_width
                if current_x > max_x:
                    break
                lines.extend(self._line([current_x, min_y],[current_x, max_y]))
                current_x += etch_width
        for line in lines:
            etches.append(EtchLine(line[0], line[1], etch_width=etch_width))
        return etches
    
    
    # Returns brick texture
    # typical brick is 215mm x 65mm (x 102.5mm depth) with 10mm motar
    def _get_etches_bricks(self):
        #print ("Get etches bricks")
        etch_width = self.settings["brick_etch"]
        brick_height = self.settings["brick_height"]
        brick_width = self.settings["brick_width"]
        return self._get_etches_rects(etch_width, brick_height, brick_width)
        #print ("Etches bricks finished")
    
    # Return tile texture - regular rectangular tiles (eg. slate)
    # Like bricks but larger and possibly thinner etch
    def _get_etches_tiles(self):
        etch_width = self.settings["tile_etch"]
        tile_height = self.settings["tile_height"]
        tile_width = self.settings["tile_width"]
        return self._get_etches_rects(etch_width, tile_height, tile_width)
    
    # Returns rect used for bricks / rect tiles (known as tiles)
    # Applies rows of staggered rectangles (such as bricks)
    def _get_etches_rects(self, etch_width, rect_height, rect_width):
        #print ("Getting rects")
        #print ("Get etches rects")
        lines = []
        etches = []
        
        min_x = self.polygon.bounds[0]+1
        max_x = self.polygon.bounds[2]-1
        min_y = self.polygon.bounds[1]+1
        max_y = self.polygon.bounds[3]-1
        min_rect_width = rect_width / 2
        min_rect_height = rect_height / 4
        # Generate horizontal lines across full width of wall
        # Starting bottom left
        current_y = self.polygon.bounds[3]-1
        current_x = min_x
        # row alternate between 0 and 1 (0 - start full brick, 1 - start 1/2 brick)
        row = 0
        half_etch = etch_width / 2    # half of the etch width, need to use this multiple times 
        # One row at a time - create individual brick markers then add line across top
        while current_y > min_y:
            current_x = min_x
            if row == 0:
                current_x += rect_width
            else:
                current_x += rect_width / 2
            #  short lines for end of each brick
            while current_x < max_x:
                # Draw vertical line
                lines.extend(self._line([current_x, current_y - half_etch], [current_x, current_y-(rect_height+half_etch)]))
                current_x += rect_width + etch_width
                if current_x + min_rect_width > max_x:
                    break
            # flip row between odd and even (eg full brick vs half brick)
            row = 1 - row
            current_y -= (rect_height + etch_width)
            lines.extend(self._line([min_x, current_y],[max_x, current_y]))
        
        for line in lines:
            etches.append(EtchLine(line[0], line[1], etch_width=etch_width))
        #print ("Rects done")
        return etches
    
    
    # Break task into small functions, these are multistep operations
    # Mostly these are horizontal and vertical lines representing joins between materials
    # such as wood joints and / or motar for bricks
    # Eg for a line call _line
    # This calls _line_zone to ensure that it is within the bounds of the wall
    # then calls _line_exclude_all to remove any parts of line that may be in a feature
    # which in turns handles each line against each polygon
    # Each of these returns a list as it maybe that the line needs to be subdivided
    
    
    def _line(self, start, end):
        segments = self._line_zone ((start, end))
        if segments == []:
            return []
        return segments
#     
#     def line_remove_features (self, segments)
#         final_lines = []
#         for segment in segments:
#             sub_lines = self._line_exclude_all(segment)
#             if sub_lines != []:
#                 final_lines.extend(sub_lines)
#         return final_lines
            
        
    # Get lines within wall (or texture zone if that is defined instead)
    # Note that there are ways that this could be optimized
    def _line_zone(self, line):
        # Check if line is completely outside the zone
        # If so return no line
        linestring = LineString([line[0], line[1]])

        return shapely_to_linelist (linestring.intersection(self.polygon))

    # Check if the line needs to be excluded, or subdivided due to exclusion areas (features)    
    def _line_exclude_all(self, line):
        # convert excludes into Polygons
        exclude_poly = []
        for exclude in self.excludes:
            exclude_poly.append(Polygon(exclude))
            
        # Convert line to list of lines (so can apply multiple segments to each exclude)
        segments = [line]
            
        # Check a poly at a time against all segments
        # Then update segments with any remaining / subdivided
        # then repeat for next polygon
        for poly in exclude_poly:
            new_segments = []
            for this_segment in segments:
                #returned_segments = self._line_exclude_poly(this_segment, poly)
                linestring = LineString(this_segment)
                returned_segments = shapely_to_linelist(linestring.difference(poly))
                if returned_segments != []:
                    new_segments.extend(returned_segments)
            # If new segments empty, then fully exclude line so return
            if new_segments == []:
                return []
            else:
                segments = new_segments.copy()
        return segments