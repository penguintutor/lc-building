import svgwrite
from wall import *


cut_stroke = svgwrite.rgb(0, 0, 0, '%')
etch_stroke = svgwrite.rgb(30, 30, 30, '%')
# don't show filled in - use fill in laser cutter
etch_fill = "none"

filename = "testoutput.svg"

# Typical dimensions for an Apex (pointed pitched roof)
# depth is from front door to rear
# dimensions in mm
# eg. of 6 x 4 shed
depth = 1826
width = 1180
wall_height = 1864
roof_height = 2122
roof_depth = 1882
roof_width = 1342 # width relative to floor (not actual size of roof)
door_width = 800
door_height = 1800

wood_height = 150
wood_etch = 10

building_type="shed"
building_subtype="apex"

scales = {
    'N': 148,
    'OO': 76.2,
    'HO': 87,
    'TT': 120,
    'G': 22.5
    }

#scale = "OO"
scale = "G"

# Export in grid 3 wide
grid_width = 3
# Start position
offset = [0, 0]
spacing = 10
num_objects = 0
current_height = 0 # Only need for height to track which piece needs most space


dwg = svgwrite.Drawing(filename, profile='tiny')


# Create side wall
walls = [
    RectWall(depth, wall_height, scales[scale]),
    RectWall(depth, wall_height, scales[scale]),
    ApexWall(width, roof_height, wall_height, scales[scale]),
    ApexWall(width, roof_height, wall_height, scales[scale])
    ]

# Add wood etching to all walls
for wall in walls:
    wall.add_wood_etch (wood_height, wood_etch)

for wall in walls:
    # Is this modulo grid_width if so then start next line
    # Will match on first one - which will add spacing
    if num_objects % grid_width == 0:
        # Reset x and extend y
        offset [0] = spacing
        offset [1] = offset[1] + current_height + spacing
    num_objects += 1
    # At end of adding each shape we extend the x position (but not the y)
    # Get overall dimensions for positioning
    num_objectsect_size = wall.get_scale_maxsize()
        
    # get the cuts
    cuts = wall.get_scale_cuts()
    for cut in cuts:
        if (cut[0] == "line"):
            start_line = (offset[0]+cut[1][0], offset[1]+cut[1][1])
            end_line = (offset[0]+cut[2][0], offset[1]+cut[2][1])
            dwg.add(dwg.line(start_line, end_line, stroke=cut_stroke))
        elif (cut[0] == "rect"):
            start_rect = (offset[0]+cut[1][0], offset[1]+cut[1][1])
            dwg.add(dwg.rect(start_rect, cut[2], stroke=cut_stroke, fill="none"))
            
    # Get the etching
    etches = wall.get_scale_etches()
    if etches != None:
        for etch in etches:
            if (etch[0] == "line"):
                start_line = (offset[0]+etch[1][0], offset[1]+etch[1][1])
                end_line = (offset[0]+etch[2][0], offset[1]+etch[2][1])
                dwg.add(dwg.line(start_line, end_line, stroke=etch_stroke))
            elif (etch[0] == "rect"):
                start_rect = (offset[0]+etch[1][0], offset[1]+etch[1][1])
                dwg.add(dwg.rect(start_rect, etch[2], stroke=etch_stroke, fill=etch_fill))
            elif (etch[0] == "polygon"):
                # iterate over each of the points to make a new list
                new_points = []
                for point in etch[1]:
                    new_points.append(((offset[0]+point[0]),(offset[1]+point[1])))
                dwg.add(dwg.polygon(new_points, stroke=etch_stroke, fill=etch_fill))
                
        # Add offset for the end - do even if this is last on row as it will be reset when next line
        offset[0] = offset[0] + spacing  + num_objectsect_size[0]
        if num_objectsect_size[1] > current_height :
            current_height = num_objectsect_size[1]
            
            
#dwg.add(dwg.text('Test', insert=(10, 30), stroke=etch_stroke, fill=etch_fill))
dwg.save()