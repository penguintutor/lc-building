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
