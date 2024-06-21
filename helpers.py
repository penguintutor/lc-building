import math

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
