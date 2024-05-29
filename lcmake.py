import svgwrite
from laser import *
from wall import *
from wallfactory import *
from buildingdata import *
from scale import *
from svgout import *
from buildingtemplate import *
from featuretemplate import *

# Same stroke width for all as used for laser
stroke_width = 1
cut_stroke = svgwrite.rgb(0, 0, 0, '%')
etch_stroke = svgwrite.rgb(30, 30, 30, '%')
# don't show filled in - use fill in laser cutter
etch_fill = "none"

filename = "testoutput.svg"

building_template = BuildingTemplate()
building_template.load_template("templates/building_shed_apex_1.json")


building = BuildingData()
# Copy all date from template into building data
building.set_all_data(building_template.get_data())

# Get all the values from 
bdata = building.get_values()

wood_height = 150
# Width of a wood etch line (boundry between wood)
wood_etch = 10


# Setting option (if set then a line is returned as a polygon based on etch_line_width
# Normally want as True as Lightburn will not allow lines as etches (recommended)
# If you prefer to edit as a line (eg. ink InkScape) then you can set to False
# Note that the co-ordinates will be centre of the line so will be extended in all directions
# This may have implications for overlapping 
etch_as_polygon = True
# Set width of etch lines (eg. door outside)
# If etch as polygon True then this value moust be set
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
# Alternative to door_outside_cuts - etch instead
# Commonly used for small scales - otherwise need to create hinge to mount door back on
door_outside_etches = [
    # bottom left to top left
    EtchLine ((door_pos[0], door_pos[1]+door_size[1]), (door_pos[0], door_pos[1])),
    # top line
    EtchLine ((door_pos[0], door_pos[1]), (door_pos[0] + door_size[0], door_pos[1])),
    # top right to bottom right
    EtchLine ((door_pos[0] + door_size[0], door_pos[1]), (door_pos[0] + door_size[0], door_pos[1]+door_size[1]))
    ]
# Feature etches have to be defined explicitly 
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
# Eg. size of a small laser cutter / 3D printer
doc_size_mm = (200, 200)

sc = Scale(scale)
# Create laser class so pass objects / settings for laser parent
laser = Laser("master", None)
# Pass scale instance to laser class
laser.set_scale_object(sc)

svgsettings = {}
svgsettings['docsize'] = sc.mms_to_pixels(doc_size_mm)
svgsettings["strokewidth"] = stroke_width
svgsettings["cutstroke"] = cut_stroke
svgsettings["etchstroke"] = etch_stroke
svgsettings["etchfill"] = etch_fill
svgsettings["etchaspolygon"] = etch_as_polygon
svg = SVGOut(filename, svgsettings)

wf = WallFactory()

walls = []
for wall in building.get_walls():
    #print (f"Wall is {wall}")
    wall_values = []
    for value in wall[1]:
        #print (f"Value {value}")
        wall_values.append(bdata[value])
    walls.append(wf.create_wall(wall[0], wall_values))
    #print (f"Created Wall {walls[len(walls)-1]}")


# Create walls
#walls = [
#    RectWall(depth, wall_height),
#    RectWall(depth, wall_height),
#    ApexWall(width, roof_height, wall_height),
#    ApexWall(width, roof_height, wall_height),
    # Roof is a type of "wall" depth is first followed by width
    # For type = "apex" then roof is half of shed - but width is still width of building
    # Create two roof segments - although identical , one for left one for right
#    RoofWall(depth, width, roof_height-wall_height, "apex", roof_right_overlap, roof_left_overlap, roof_front_overlap, roof_rear_overlap),
#    RoofWall(depth, width, roof_height-wall_height, "apex", roof_right_overlap, roof_left_overlap, roof_front_overlap, roof_rear_overlap)
#    ]

# Add wood etching to all walls
for wall in walls:
    if wall.get_type() != "roof":
        wall.add_wood_etch (wood_height, wood_etch)
    
# Add window to wall 0
walls[1].add_feature("window", window_pos, window_size, cuts=window_cuts, etches=window_etches, settings={"windowtype":"rect"})
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
        svg.set_offset(offset)
    num_objects += 1
    # At end of adding each shape we extend the x position (but not the y)
    # Get overall dimensions for positioning
    num_objectsect_size = sc.convert(wall.get_maxsize())
        
    # get the cuts
    for cut in wall.get_cuts():
        svg.add_cut(cut)
            
    # Get the etching
    etches = wall.get_etches()
    if etches != None:
        for etch in etches:
            svg.add_etch(etch)
                
    # Add offset for the end - do this even if this is last on column as it will be reset when next line
    offset[0] = offset[0] + spacing  + num_objectsect_size[0]
    svg.set_offset(offset)
    if num_objectsect_size[1] > current_height :
        current_height = num_objectsect_size[1]
            
svg.save()
