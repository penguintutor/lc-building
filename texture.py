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
        etch_width = self.settings["brick_etch"]
        brick_height = self.settings["brick_height"]
        brick_width = self.settings["brick_width"]
        return self._get_etches_rects(etch_width, brick_height, brick_width)
    
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
        return etches
    
    
    # Break task into small functions, these are multiste            etches.append(EtchLine(line[0], line[1], etch_width=etch_width))p operations
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
        final_lines = []
        for segment in segments:
            sub_lines = self._line_exclude_all(segment)
            if sub_lines != []:
                final_lines.extend(sub_lines)
        return final_lines
            
        
    # Get lines within wall (or texture zone if that is defined instead)
    # Note that there are many ways that this could be optomised, but based on usage (ie. typical builing size)
    # this is efficient enough
    def _line_zone(self, line):
        return_lines = []
        # Get angle if needed later
        angle = get_angle(line)
        # Is start of the line within the wall
        start_point = Point(line[0])
        end_point = Point(line[1])
        # If start is outside the zone, then increment until it is within the zone
        while not start_point.within(self.polygon):
            # Increase start_point until within zone or reach end
            new_pos = add_distance_to_points ((start_point.x,start_point.y), 1, angle)
            start_point = Point(*new_pos)
            # If reach end of zone line not within zone
            if start_point.x > self.polygon.bounds[2] or start_point.y < self.polygon.bounds[1]:
                return []
        # Now check the end_pos
        while not end_point.within(self.polygon):
            # Decrease end_point until within zone or go out of bounds
            new_pos = add_distance_to_points ((end_point.x,end_point.y), -1, angle)
            end_point = Point(*new_pos)
            # Should complete before we get here, but this ensures we exit if we don't
            if end_point.x < self.polygon.bounds[0] or end_point.y > self.polygon.bounds[3]:
                return []

        # Start and end is within the zone (wall)
        # Does it cross any of the lines of the zone - in which case need to split into different parts
        # Convert the points into a lineString and poly to lines so can test for intersecting
        line_string = LineString([start_point, end_point])
        poly_as_lines = LineString(self.polygon.boundary.coords)
        
        new_pos = (end_point.x, end_point.y)
        while line_string.intersects(poly_as_lines):
            # start from end of line_string until no longer intersects
            new_pos = add_distance_to_points (new_pos, -1, angle)
            line_string = LineString([start_point, new_pos])
            # Should complete before we get here, but this ensures we exit if we don't
            if new_pos[0] < self.polygon.bounds[0] or new_pos[1] > self.polygon.bounds[3]:
                return []
        # Add this line to the return
        return_lines.append(([start_point.x, start_point.y],new_pos))
        # If new_pos is unchanged, then just one line, but if not then we've created a segment
        # so add another segment for the rest of the line and try again
        if new_pos[0] != end_point.x or new_pos[1] != end_point.y:
            # Extend new_pos and use that as start of next line, use the original end_point as the end of the line
            new_start_pos = add_distance_to_points (new_pos, 1, angle)
            next_segments = self._line_zone((new_start_pos, (end_point.x, end_point.y)))
            if next_segments != []:
                return_lines.extend(next_segments)
        return return_lines
            
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
                returned_segments = self._line_exclude_poly(this_segment, poly)
                if returned_segments != []:
                    new_segments.extend(returned_segments)
            # If new segments empty, then fully exclude line so return
            if new_segments == []:
                return []
            else:
                segments = new_segments.copy()
        return segments
        

    # Check for one line (or line segment) against poly
    # If fully exclude then return empty list
    # If not exclude return line
    # Otherwise subdivide
    ## todo not fully tested for splitting multiple segments 
    def _line_exclude_poly(self, line, poly):
        this_line = [*line]
        line_string = LineString (this_line)
        # If not intersection then return original line
        if not poly.intersects(line_string):
            return [this_line]
        # if completely within an exclude then return empty
        if poly.contains(line_string):
            return []
        # Need to shorten subdivide. Start at beginning of line
        # If beginning of the line is in the zone then increase until it is outside of the zone
        angle = get_angle(this_line)
        start_point = Point(this_line[0])
        end_point = Point(this_line[1])
        while start_point.within(poly) or start_point.intersects(poly):
            new_pos = add_distance_to_points((start_point.x,start_point.y), 1, angle)
            start_point = Point(*new_pos)
            # No need for sanity check as already established that it is not completely within
            # exclude area from earlier check, so this will always complete when start is outside of zone
        this_line[0] = [start_point.x, start_point.y]
        # Are we no longer intersecting - in which case we can return new line
        line_string = LineString(this_line)
        if not poly.intersects(line_string):
            return [this_line]
        # Also try shortening from end point
        while end_point.within(poly) or end_point.intersects(poly):
            new_pos = add_distance_to_points((end_point.x,end_point.y), -1, angle)
            end_point = Point(*new_pos)
            # No need for sanity check as already established that it is not completely within
            # exclude area from earlier check, so this will always complete when start is outside of zone
        this_line[1] = [end_point.x, end_point.y]
        # Are we no longer intersecting - in which case we can return new line
        line_string = LineString(this_line)
        # If reach here then start and end are not in exclude zone, but line does pass through exclude zone
        # So find first point that is in exclude zone and split at that point
        new_point = Point(this_line[0])
        while not new_point.within(poly):
            new_pos = add_distance_to_points((new_point.x,new_point.y), 1, angle)
            new_point = Point(*new_pos)
        # end of first segment is now new point -1
        end_segment = add_distance_to_points((new_point.x,new_point.y), -1, angle)
        return_line = [[this_line[0],end_segment]]
        # Use new_point as start of next segment and repeat whole process again recursively
        next_segments = self._line_exclude_poly([[new_point.x,new_point.y],this_line[1]], poly)
        if next_segments != []:
            return_line.extend(next_segments)
        return return_line
    
