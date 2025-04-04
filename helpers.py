import math
import copy
from shapely import Point, Polygon, LineString
from laser import EtchLine

# Helper functions
def get_angle (line):
    # Note dy goes from top to bottom as y axis is inverted
    dx = line[0][0] - line[1][0]
    dy = line[1][1] - line[0][1]
    theta = math.atan2(dy, dx)
    # subtract 90degs due to relative start pos - start from straight down (with y in neg direction)
    angle = 360 - ((math.degrees(theta) - 90  ) * -1)
    # If angle is 360 then make 0
    if angle >= 360:
        angle -= 360
    return angle


# Converts a rectangle to a list of points
def rect_to_polygon (pos, width, height):
    polygon = []
    polygon.append(pos)
    polygon.append((pos[0]+width, pos[1]))
    polygon.append((pos[0]+width, pos[1]+height))
    polygon.append((pos[0], pos[1]+height))
    polygon.append(pos)
    return polygon

def get_distance (start, end):
    return math.hypot (end[0]-start[0], end[1]-start[1])
    
# Adds a distance to an existing point and based on angle work out
# new x and y co-ordinates
def add_distance_to_points (start, distance, angle):
    newx = round(start[0] + (distance * math.sin(math.radians(angle))))
    newy = round(start[1] + (distance * math.cos(math.radians(angle))))
    return (newx, newy)

# Check that start to end is less than (-difference), greater than (+difference), same as (0) max_dist
def check_distance (start, end, max_dist):
    distance = get_distance(start, end)
    return max_dist - distance

# Takes shapely reponse and returns list of points for corresponding lines 
def shapely_to_linelist (intersect):
    return_list = []
    if intersect.geom_type == "MultiLineString":
        for linestring in intersect.geoms:
            return_list.append([linestring.coords[0], linestring.coords[1]])
            #print (f"Linestring {linestring}")
    elif intersect.geom_type == "LineString":
        # Ignore empty entries
        if (intersect.length > 0):
            #print (f"Linestring {intersect}")
            return_list.append([intersect.coords[0], intersect.coords[1]])
    elif intersect.geom_type == "MultiPoint":
        #print (f"MultiPoint {intersect}")
        return_list.append([[intersect.bounds[0], intersect.bounds[1]], [intersect.bounds[2], intersect.bounds[3]]])
    return return_list

# Keeps responses as linestrings (or converts to line strings)
def shapely_to_linestrings (intersect):
    return_list = []
    if intersect.geom_type == "MultiLineString":
        for linestring in intersect.geoms:
            return_list.append(linestring)
            #print (f"Linestring {linestring}")
    elif intersect.geom_type == "LineString":
        # Ignore empty entries
        if (intersect.length > 0):
            #print (f"Linestring {intersect}")
            return_list.append(intersect)
    elif intersect.geom_type == "MultiPoint":
        #print (f"MultiPoint {intersect}")
        return_list.append(Linestring(intersect))
    return return_list

# Removes features from etchlines and returns as etchlines
def line_remove_features (lines, excludes):
    if excludes == []:
        return copy.copy(lines)
    final_lines = []
    #print (f"Removing features {lines}, {excludes}")
    if lines == []:
        return final_lines
    exclude_poly = []
   
    for exclude in excludes:
        exclude_poly.append(Polygon(exclude))
    
    # Check a line at a time against all polys
    for this_line in lines:
        # Convert etchline into a linestring and get width & strength for use later
        # Place linestring into list so can iterate over for each polygon
        linestrings = [LineString(this_line.get_line())]
        etch_width = this_line.etch_width
        strength = this_line.strength
        
        for poly in exclude_poly:
            new_linestrings = []
            for linestring in linestrings:
                new_linestrings.extend(shapely_to_linestrings(linestring.difference(poly)))
            #  linestrings replaced with new_linestrings so that we apply next poly on the updated list
            linestrings = new_linestrings
        # applied against all polys so now add to final lines as an etchline
        for linestring in linestrings:
            final_lines.append(EtchLine(linestring.coords[0], linestring.coords[1], etch_width=etch_width, strength=strength))
        # now apply to next line
    return final_lines



#     # Check a poly at a time against all segments
#     # Then update segments with any remaining / subdivided
#     # then repeat for next polygon
#     for poly in exclude_poly:
#         new_segments = []
#         for this_segment in lines:
#             #print (f"Get line {this_segment.get_line()}")
#             #returned_segments = self._line_exclude_poly(this_segment, poly)
#             linestring = LineString(this_segment.get_line())
#             etch_width = this_segment.etch_width
#             strength = this_segment.strength
#             
#             returned_segments = shapely_to_linelist(linestring.difference(poly))
#             for new_segment in returned_segments:
#                 final_lines.append(EtchLine(new_segment[0], new_segment[1], etch_width=etch_width, strength=strength))
