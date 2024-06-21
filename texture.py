# Texture is an etch applied to a wall (or similar)
# Not shown where conflict with a feature (eg. window)
# Creates an instance for each element - then can use to detect
# if it needs to be removed because of other features

from laser import *
from helpers import *
from shapely import Point, Polygon, LineString

# Texture needs to be applied with direction either vertical or horizontal
# Could have diagonal elements (eg. polygon representing stone), but still define
# by horizontal or vertical
# When it overlaps a features then the entire texture will be broken at that point as it
# doesn't make sense to have half a texture - eg. half a morter between brick and window
# If defined as horizontal then it is broken full across y and if vertical then fully across x

# Only work in mm
# Wall should handle conversion to pixels

class Texture():
    def __init__ (self, points, style=None):
        self.points = points
        # Convert points to a polygon
        self.polygon = Polygon(points)
        self.disable = False   # Allows to disable completely if not required
        self.exclude = []      # Exclude is defined as (minx, miny, endx, endy)
        
    # Areas to exclude for the output
    # Ensure this is only called once per instance
    # Normally textures only exist during export so isn't normally
    # a problem
    def _old_exclude_etch(self, points):
        # check if collide if so add to exclusions
        # First look if texture totally enclosed (if so then remove completely)
        # Eg. Brick within a window position
        if (self.min_x >= startx and self.min_y >= starty and self.max_x <= endx and self.max_y <= endy):
            # completely disable this part of the texture
            self.disable = True
            # Add to exclude (although most likely not required)
            self.exclude.append(startx, starty, endx, endy)
        # If not fully contained then does it overlap (ie. either start or end of exclude is
        # within the rect of the texture
        elif (startx >= self.min_x and startx <= self.max_x and
              (starty <= self.min_y and endy >= self.min_y) or
              (starty <= self.max_y and endy > self.max_y)):
            self.exclude.append((startx, starty, endx, endy))
        elif (endx >= self.min_x and endx <= self.min_x and
              (starty <= self.min_y and endy >= self.min_y) or
              (starty <= self.max_y and endy > self.max_y)):
            self.exclude.append((startx, starty, endx, endy))
    
    
    def get_etches(self):
        pass
    
    
    # Break task into small functions, these are multistep operations
    # Mostly these are horizontal and vertical lines representing joins between materials
    # such as wood joints and / or motar for bricks
    # Eg for a line call _line
    # This calls _line_zone to ensure that it is within the bounds of the wall
    # then calls _line_feature to remove any parts of line that may be in a feature
    # Each of these returns a list as it maybe that the line needs to be subdivided
    
    
    def _line(self, start, end):
        segments = self._line_zone ((start, end))
        if segments == []:
            return []
        final_lines = []
        #for segment in segments:
        #    final_lines.extend(self._line_features(segment))
        #return final_lines
        return segments
            
        
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
            
        
        
        
    def _line_features(self, line):
        return line
    
    
    
    
    # Return a list even if only one element
    # Old version
    def get_etches_rect(self):
        if self.exclude == True:
            return None
        if len(self.exclude) == 0:
        # If no exclusions then just return a single rectangle
            #return [("rect", (self.start_pos[0], self.start_pos[1]), (self.dimension[0], self.dimension[1]))]
            return [EtchRect((self.start_pos[0], self.start_pos[1]), (self.dimension[0], self.dimension[1]))]
        # Handle partial exclusion
        rects = []
        if self.direction == "horizontal":
            # Get sorted list of exclusions by x
            sorted_list = sorted(self.exclude, key=lambda sortkey: sortkey[0])
            current_x = self.start_pos[0]
            for this_exclude in sorted_list:
                # If left rectangle width = 0 then skip to next
                if this_exclude[0] <= current_x:
                    current_x = this_exclude[2]
                    continue
                # create rect from current pos to this exclude
                #rects.append(("rect", (current_x, self.start_pos[1]), (this_exclude[0]-current_x, self.dimension[1])))
                rects.append(EtchRect((current_x, self.start_pos[1]), (this_exclude[0]-current_x, self.dimension[1])))
                # Set current pos to end of exclude
                current_x = this_exclude[2]
            # if not reached end of wall then add final rectangle
            if current_x < self.start_pos[0] + self.dimension[0]:
                #rects.append(("rect", (current_x, self.start_pos[1]), (self.dimension[0]-current_x, self.dimension[1])))
                rects.append(EtchRect ((current_x, self.start_pos[1]), (self.dimension[0]-current_x, self.dimension[1])))
        if self.direction == "vertical":
            # Get sorted list of exclusions by y
            sorted_list = sorted(self.exclude, key=lambda sortkey: sortkey[1])
            current_y = self.start_pos[1]
            for this_exclude in sorted_list:
                # If left rectangle width = 0 then skip to next
                if this_exclude[1] <= current_y:
                    current_y = this_exclude[3]
                    continue
                # create rect from current pos to this exclude
                #rects.append(("rect", (self.start_pos[0], current_y ), (self.dimension[1], this_exclude[1]-current_y)))
                rects.append(EtchRect ((self.start_pos[0], current_y ), (self.dimension[1], this_exclude[1]-current_y)))
                # Set current pos to end of exclude
                current_y = this_exclude[3]
            # if not reached end of wall then add final rectangle
            if current_y < self.start_pos[1] + self.dimension[1]:
                #rects.append(("rect", (self.start_pos[0], current_y), (self.dimension[1], self.dimension[1]-current_y)))
                rects.append(EtchRect ((self.start_pos[0], current_y), (self.dimension[1], self.dimension[1]-current_y)))
        
        return rects
                
            
        
    