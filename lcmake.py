# LC make takes an existing building and generates the image files
import svgwrite
from laser import *
from wall import *
from buildingdata import *
from scale import *
from svgout import *
from buildingtemplate import *
from featuretemplate import *
from interlocking import *
from lcconfig import LCConfig


config = LCConfig()


filename = "output/g-weigh_bridge-1.svg"

#building_template = BuildingTemplate()
#building_template.load_template("templates/building_shed_apex_1.json")

#building_datafile = "buildings/shed_1.json"
building_datafile = "buildings/weigh_bridge_1.json"
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

# Feature positions are top left
# Note y=0 is top of roof height 

# If set to percent then gives percentage complete as generate each wall
#(note does not take into consideration that some have textures and some don't)
progress = "percent"




#scale = "OO"
scale = "G"


# Export in grid 3 wide
grid_width = 3
# Start position
offset = [0, 0]
# spacing is distance beteen objects (eg. walls) when exported to SVG
spacing = 50
num_objects = 0
current_height = 0 # Only need for height to track which piece needs most space

# Eg. size of a small laser cutter / 3D printer
doc_size_mm = (600, 600)

sc = Scale(scale)

# Pass scale instance to laser class
Laser.sc = sc
# Use scale to apply reverse scale to actual material_thickness
material_thickness = bdata["material_thickness"]
scale_material = sc.reverse_scale_convert(material_thickness)
# Set material thickness for Interlocking (class variable)
Interlocking.material_thickness = scale_material
# Set default etchline width
EtchLine.global_etch_width = config.etch_line_width

Wall.settings["outertype"] = bdata["outertype"]

# Convert configuration into SVG settings for output
svgsettings = {}

svgsettings['docsize'] = sc.mms_to_pixels(doc_size_mm)
svgsettings["strokewidth"] = config.stroke_width
svgsettings["cutstroke"] = svgwrite.rgb(*config.cut_stroke)

# Convert config colors into svgwrite values
etch_strokes = []
for stroke_color in config.etch_strokes:
    etch_strokes.append(svgwrite.rgb(*stroke_color))

svgsettings["etchstrokes"] = etch_strokes
svgsettings["etchfill"] = config.etch_fill
svgsettings["etchaspolygon"] = config.etch_as_polygon
svg = SVGOut(filename, svgsettings)

walls = []
for wall in building.get_walls():
    # Convert from string values to values from bdata
    walls.append(Wall(wall[0], wall[1], wall[2]))
    
# Add roofs (loads differently but afterwards is handled as a wall)
for roof in building.get_roofs():
    walls.append(Wall(roof[0], roof[1], roof[2]))

for texture in building.get_textures():
    # If not area then default to entire wall
    area = []
    if 'area' in texture:
        area = texture['area']
    walls[texture["wall"]].add_texture(texture["type"], area, texture["settings"] )
    
for feature in building.get_features():
    # Features takes a polygon, but may be represented as more basic rectangle.
    pos = feature["parameters"]["pos"]
    polygon = []
    # If no points provided then convert rectangle into a polygon
    if ("exclude" in feature["parameters"].keys()):
        # For each point then make relative to the pos
        for this_point in feature["parameters"]["exclude"]:
            polygon.append((this_point[0], this_point[1]))
    else:
        width = feature["parameters"]["width"]
        height = feature["parameters"]["height"]
        polygon = rect_to_polygon((0,0), width, height)
        
    walls[feature["wall"]].add_feature(feature["type"], feature["template"], pos, polygon,
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
        # il_type has default but can add others in future
        il_type = "default"
        if "type" in il:
            il_type = il["type"]
        walls[il["primary"][0]].add_interlocking(il["step"], il["primary"][1], "primary", reverse, il_type, parameters)
        reverse = ""
        if len(il["secondary"]) > 2:
            reverse = il["secondary"][2]
        walls[il["secondary"][0]].add_interlocking(il["step"], il["secondary"][1], "secondary", reverse, il_type, parameters)
    
    
   
# Create output
# Track wall number for simple progress chart
num_walls = len(walls)
wall_num = 0
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
    for cut in wall.get_cuts(True, True):
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
    wall_num += 1
    if (progress == "percent"):
        print (f"{round((wall_num/num_walls) * 100)} % complete")
            
svg.save()
