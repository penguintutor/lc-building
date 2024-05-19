import svgwrite
from laser import *
from wall import *
from scale import *

# Same stroke width for all as used for laser
stroke_width = 1
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


# Overlap is different for each side
# Eg. may have a canope for front
roof_right_overlap = 100
roof_left_overlap = 100
roof_front_overlap = 50
roof_rear_overlap = 50

wood_height = 150
# Width of a wood etch line (boundry between wood)
wood_etch = 10
# Set width of other etch_lines (eg. door outside)
etch_line_width = 10

# Feature positions are top left
# Note y=0 is top of roof height 

# Features can have cuts and etches applied
# either manually or using textures / settings etc.
# cuts and etches can always be added to

# cuts are ethches are relative to the wall (as are all other values)
# But may want to include relative to door_pos etc.

# Example window (wall 0)
window_pos = (713, 50)
window_size = (400, 555)
window_cuts = []
window_etches = []

hinge_size = (300, 50)

# Example door (wall 2)
door_pos = (190, 322)
door_size = (800, 1800)
# Example where cut 3 sides (ie. door is to the floor)
# y direction is top to bottom - so add size to get to bottom
door_outside_cuts = [
    # bottom left to top left
    CutLine ((door_pos[0], door_pos[1]+door_size[1]), (door_pos[0], door_pos[1])),
    # top line
    CutLine ((door_pos[0], door_pos[1]), (door_pos[0] + door_size[0], door_pos[1])),
    # top right to bottom right
    CutLine ((door_pos[0] + door_size[0], door_pos[1]), (door_pos[0] + door_size[0], door_pos[1]+door_size[1]))
    ]
door_cuts = []
door_outside_etches = [
    # bottom left to top left
    EtchLine ((door_pos[0], door_pos[1]+door_size[1]), (door_pos[0], door_pos[1])),
    # top line
    EtchLine ((door_pos[0], door_pos[1]), (door_pos[0] + door_size[0], door_pos[1])),
    # top right to bottom right
    EtchLine ((door_pos[0] + door_size[0], door_pos[1]), (door_pos[0] + door_size[0], door_pos[1]+door_size[1]))
    ]
# vertical wood effect
door_etches = [
    EtchRect ((door_pos[0]+175, door_pos[1]), (wood_etch, door_size[1])),
    EtchRect ((door_pos[0]+325, door_pos[1]), (wood_etch, door_size[1])),
    EtchRect ((door_pos[0]+475, door_pos[1]), (wood_etch, door_size[1])),
    EtchRect ((door_pos[0]+625, door_pos[1]), (wood_etch, door_size[1])),
    # Hinges
    EtchPolygon (((door_pos[0]+door_size[0], door_pos[1]+int(door_size[1]*0.15)),
                  (door_pos[0]+door_size[0]-hinge_size[0], door_pos[1]+int(door_size[1]*0.15) + (hinge_size[1]/2)),
                  (door_pos[0]+door_size[0], door_pos[1]+int(door_size[1]*0.15) + hinge_size[1]),
                  )),
    EtchPolygon (((door_pos[0]+door_size[0], door_pos[1]+int(door_size[1]*0.5)-(hinge_size[1]/2)),
                  (door_pos[0]+door_size[0]-hinge_size[0], door_pos[1]+int(door_size[1]*0.5)),
                  (door_pos[0]+door_size[0], door_pos[1]+int(door_size[1]*0.5) + (hinge_size[1]/2)),
                  )),
    EtchPolygon (((door_pos[0]+door_size[0], door_pos[1]+int(door_size[1]*0.85)),
                  (door_pos[0]+door_size[0]-hinge_size[0], door_pos[1]+int(door_size[1]*0.85) + (hinge_size[1]/2)),
                  (door_pos[0]+door_size[0], door_pos[1]+int(door_size[1]*0.85) + hinge_size[1]),
                  )),
    ]

building_type="shed"
building_subtype="apex"
# Do we "etch" or "cut" the door out
door_burn="etch"
if door_burn == "cut":
    door_cuts.extend(door_outside_cuts)
elif door_burn == "etch":
    door_etches.extend(door_outside_etches)

scale = "OO"
#scale = "G"

# Dummy EtchLine entry allowing us to set parameters for all EtchLines
global_etch_line = EtchLine((0,0),(0,0))
# Set width for all etch lines
global_etch_line.set_global_width(etch_line_width)

# Export in grid 3 wide
grid_width = 3
# Start position
offset = [0, 0]
# spacing is distance beteen objects (eg. walls) when exported to SVG
spacing = 10
num_objects = 0
current_height = 0 # Only need for height to track which piece needs most space

# Approx 200 x 200mm in pixels
doc_size = (710, 710)

dwg = svgwrite.Drawing(filename, profile='tiny', size=(str(doc_size[0]),str(doc_size[1])))

sc = Scale(scale)


# Create walls
walls = [
    RectWall(depth, wall_height),
    RectWall(depth, wall_height),
    ApexWall(width, roof_height, wall_height),
    ApexWall(width, roof_height, wall_height),
    # Roof is a type of "wall" depth is first followed by width
    # For type = "apex" then roof is half of shed - but width is still width of building
    # Create two roof segments - although identical , one for left one for right
    RoofWall(depth, width, roof_height-wall_height, "apex", roof_right_overlap, roof_left_overlap, roof_front_overlap, roof_rear_overlap),
    RoofWall(depth, width, roof_height-wall_height, "apex", roof_right_overlap, roof_left_overlap, roof_front_overlap, roof_rear_overlap)
    ]

# Add wood etching to all walls
for wall in walls:
    if wall.get_type() != "roof":
        wall.add_wood_etch (wood_height, wood_etch)
    
# Add window to wall 0
walls[0].add_feature("window", window_pos, window_size, cuts=window_cuts, etches=window_etches, settings={"windowtype":"rect"})
# Add door to apex wall 2
walls[2].add_feature("door", door_pos, door_size, cuts=door_cuts, etches=door_etches)
    
# Create output
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
    num_objectsect_size = sc.convert(wall.get_maxsize())
        
    # get the cuts
    cuts = wall.get_cuts()
    for cutobj in cuts:
        cut = cutobj.get_cut()
        if (cut[0] == "line"):
            # start cut is relative to object
            start_cut = sc.convert(cut[1])
            # start line includes offset
            start_line = (offset[0]+start_cut[0], offset[1]+start_cut[1])
            end_cut = sc.convert(cut[2])
            end_line = (offset[0]+end_cut[0], offset[1]+end_cut[1])
            dwg.add(dwg.line(start_line, end_line, stroke=cut_stroke, stroke_width=stroke_width))
        elif (cut[0] == "rect"):
            start_cut = sc.convert(cut[1])
            start_rect = (offset[0]+start_cut[0], offset[1]+start_cut[1])
            rect_size = sc.convert(cut[2])
            dwg.add(dwg.rect(start_rect, rect_size, stroke=cut_stroke, fill="none", stroke_width=stroke_width))
            
    # Get the etching
    etches = wall.get_etches()
    if etches != None:
        for etch in etches:
            if (etch.get_type() == "line"):
                # start_etch is modified start
                start_etch = sc.convert(etch.get_start())
                start_line = (offset[0]+start_etch[0], offset[1]+start_etch[1])
                end_etch = sc.convert(etch.get_end())
                end_line = (offset[0]+end_etch[0], offset[1]+end_etch[1])
                dwg.add(dwg.line(start_line, end_line, stroke=etch_stroke, stroke_width=stroke_width))
            elif (etch.get_type() == "rect"):
                start_etch = sc.convert(etch.get_start())
                start_rect = (offset[0]+start_etch[0], offset[1]+start_etch[1])
                
                rect_size = sc.convert(etch.get_size())
                dwg.add(dwg.rect(start_rect, rect_size, stroke=etch_stroke, fill=etch_fill, stroke_width=stroke_width))
            elif (etch.get_type() == "polygon"):
                # iterate over each of the points to make a new list
                new_points = []
                for point in etch.get_points():
                    sc_point = sc.convert(point)
                    new_points.append([(offset[0]+sc_point[0]),(offset[1]+sc_point[1])])
                dwg.add(dwg.polygon(new_points, stroke=etch_stroke, fill=etch_fill, stroke_width=stroke_width))
                
    # Add offset for the end - do this even if this is last on row as it will be reset when next line
    offset[0] = offset[0] + spacing  + num_objectsect_size[0]
    if num_objectsect_size[1] > current_height :
        current_height = num_objectsect_size[1]
            
            
#dwg.add(dwg.text('Test', insert=(10, 30), stroke=etch_stroke, fill=etch_fill))
dwg.save()