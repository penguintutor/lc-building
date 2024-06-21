import svgwrite
from laser import *
from wall import *
from buildingdata import *
from scale import *
from svgout import *
from buildingtemplate import *
from featuretemplate import *
from interlocking import *

# Same stroke width for all as used for laser
stroke_width = 1
cut_stroke = svgwrite.rgb(0, 0, 0, '%')
etch_stroke = svgwrite.rgb(30, 30, 30, '%')
# don't show filled in - use fill in laser cutter
etch_fill = "none"

filename = "output/g-shed-apex-1.svg"

building_template = BuildingTemplate()
building_template.load_template("templates/building_shed_apex_1.json")

building_datafile = "buildings/shed_1.json"
# Example datafile for test purposes 
#building_datafile = "buildings/test_1.json"

building = BuildingData()
building.load_file(building_datafile)
# Copy all date from template into building data

# If using a template then use the following
# building.set_all_data(building_template.get_data())

# Get the parameters and settings
bdata = building.get_values()
# Where parameters apply globally use directly in this code
# Otherwise pass to appropriate classes

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

# cuts and etches are relative to the wall (or feature within feature)
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


# Shed door has cut 3 sides (ie. door is to the floor)

# Feature etches have to be defined explicitly 
# including vertical wood effect

#scale = "OO"
scale = "G"


# Dummy EtchLine entry allowing us to set parameters for all EtchLines
global_etch_line = EtchLine((0,0),(0,0))
# Set width for all etch lines
global_etch_line.set_global_width(etch_line_width)

# Export in grid 3 wide
grid_width = 3
# Start position
offset = [0, 0]
# spacing is distance beteen objects (eg. walls) when exported to SVG
spacing = 50
num_objects = 0
current_height = 0 # Only need for height to track which piece needs most space

# Approx 200 x 200mm in pixels
# Eg. size of a small laser cutter / 3D printer
doc_size_mm = (300, 300)

sc = Scale(scale)

# Pass scale instance to laser class
Laser.sc = sc
# Use scale to apply reverse scale to actual material_thickness
material_thickness = bdata["material_thickness"]
scale_material = sc.reverse_scale_convert(material_thickness)
# Create global interlocking to update class variable
#global_interlock = Interlocking(scale_material, -1, "primary")
Interlocking.material_thickness = scale_material

Wall.settings["outertype"] = bdata["outertype"]

svgsettings = {}
svgsettings['docsize'] = sc.mms_to_pixels(doc_size_mm)
svgsettings["strokewidth"] = stroke_width
svgsettings["cutstroke"] = cut_stroke
svgsettings["etchstroke"] = etch_stroke
svgsettings["etchfill"] = etch_fill
svgsettings["etchaspolygon"] = etch_as_polygon
svg = SVGOut(filename, svgsettings)

#wf = WallFactory()

walls = []
for wall in building.get_walls():
    # Convert from string values to values from bdata
    wall_values = []
    #for value in wall[1]:
    #    wall_values.append(bdata[value])
    #print (f"{wall_values}")
    walls.append(Wall(wall[0], wall[1]))
    
# Add roofs (loads differently but afterwards is handled as a wall)
for roof in building.get_roofs():
    walls.append(Wall(roof[0], roof[1]))

for texture in building.get_textures():
    walls[texture["wall"]].add_texture(texture["type"], texture["settings"] )
    
for feature in building.get_features():
    # Features takes a polygon, but may be represented as more basic rectangle.
    pos = feature["parameters"]["pos"]
    polygon = []
    # If no points provided then convert rectangle into a polygon
    if ("exclude" in feature["parameters"].keys()):
        # For each point then make relative to the pos
        for this_point in feature["parameters"]["exclude"]:
            polygon.append((this_point[0]+pos[0], this_point[1]+pos[1]))
    else:
        width = feature["parameters"]["width"]
        height = feature["parameters"]["height"]
        polygon = rect_to_polygon(pos, width, height)
        
    walls[feature["wall"]].add_feature(pos, polygon,
                                       feature["cuts"], feature["etches"], feature["outers"])
    
# if setting is ignore interlocking then ignore any entries (wall will have il=[])
if bdata['interlocking'].lower() == "true":
    # otherwise add
    for il in building.get_interlocking():
        # Add both primary and secondary for each entry
        # parameters are optional (defines start and end positions of interlocking section)
        # These are the optional parameters which are appended
        parameter_keys = ["start", "end"]
        # if tags exist then use that if not then don't include
        parameters = {}
        for this_key in parameter_keys:
            if this_key in il.keys():
                parameters[this_key] = il[this_key]
        reverse = ""
        if len(il["primary"]) > 2:
            reverse = il["primary"][2]
        walls[il["primary"][0]].add_interlocking(il["step"], il["primary"][1], "primary", reverse, parameters)
        reverse = ""
        if len(il["secondary"]) > 2:
            reverse = il["secondary"][2]
        walls[il["secondary"][0]].add_interlocking(il["step"], il["secondary"][1], "secondary", reverse, parameters)
    
    
   
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
