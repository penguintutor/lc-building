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

# Work out if mainly in x direction or mainly in y
# based on angle of line
def get_mainly_xy (line):
    angle = get_angle (line)
    if angle <= 45 or (angle >=135 and angle <=225) or angle >= 315:
        return "x"
    else:
        return "y"