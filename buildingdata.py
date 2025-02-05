# Read and write BuildingData files
import json
import re
from lcconfig import LCConfig
from laser import *
from scale import *
from svgout import *
from wall import *
from features import *
from texture import *
from buildingtemplate import *
from featuretemplate import *
from interlocking import *
from helpers import *


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

default_pos = [0, 0]

# Views must be one of these or default to front
#allowed_views = ["front", "right", "rear", "left", "top", "bottom"]

# Create as an empty class with no data - all empty
# This allows template to be loaded afterwards or for data to be
# Added individually
class BuildingData ():
    def __init__ (self, lcconfig=None):
        self.data = {}
        if lcconfig == None:
            self.config = LCConfig()
        else:
            self.config = lcconfig
    
    # Checks the appropriate parameters for a matching value_string then evaluate
    # Returns as string
    # Used by process tokens
    def get_value_str (self, value_string):
        # if number then return directly as string
        if (is_number(value_string)):
            return (value_string)
        if value_string in self.data["parameters"]:
            return str(self.data["parameters"][value_string])
        else:
            return None
    
            
    # Better method to process_tokens which can take a single entry or list
    def process_multiple_tokens (self, token_strings):
        new_list = []
        for this_string in token_strings:
            #print (f"Processing {this_string}")
            # if this_string is actually a list then call recursively
            if type(this_string) is list:
                new_list.append(self.process_multiple_tokens (this_string))
            else:
                new_list.append(self.process_token (this_string))
        return new_list
            
    # Processes values from loaded cuts and etches looking for tokens and
    # converts the values relative to existing values
    # returns as string
    def process_token_str (self, token_string):
        new_string = ""
        # Token can be any alphanumeric and _
        # Note include numbers as token including . for fractions
        current_pos = 0
        for m in re.finditer(r"[\w.]+", token_string):
            this_token = m.group(0)
            # replace from start
            start = m.start()
            end = m.end()
            if start > current_pos:
                new_string += token_string[current_pos:start]
            new_string += self.get_value_str(this_token)
            current_pos = end
        # Any remaining chars add to the end
        if len(token_string) > current_pos:
            new_string += token_string[current_pos:]
        return new_string
        
    # Process token and perform eval to return as a number
    def process_token (self, token_string):
        # First check if it is already a number
        # Try int first as it's most likely an positive integer
        try:
            value = int (token_string)
            return value
        except ValueError:
            # print ("Not an int")
            pass
        try:
            value = float (token_string)
            return value
        except ValueError:
            # print ("Not a float")
            pass
        new_string = self.process_token_str(token_string)
        value = eval(new_string)
        return value
    
    # Load a data file
    # Overrides all data in memory
    # Returns tuple - (True / False, "Error string")
    def load_file (self, filename):
        # Keep reference to filename loaded
        self.filename = filename
        try:
            with open(filename, 'r') as datafile:
                self.data = json.load(datafile)
        except Exception as err:
            #print (f"Error {err}")
            return (False, err)
        # Simple check did we get a name
        if 'name' not in self.data.keys():
            return (False, "Invalid data file")
        return (True, "")
            
    
    # Save current data to file
    # Overwrites existing file
    # If newdata not set then write back current data, otherwise write back
    # Note this is data in buildingdata rather than updated data in builder, so
    # most likely want to specify newdata
    def save_file (self, filename, newdata = None):
        # Updates filename with new filename
        self.filename = filename
        if newdata == None:
            newdata = self.data
        json_data = json.dumps(newdata)
        try:
            with open(filename, 'w') as datafile:
                datafile.write(json_data)
        except Exeption as err:
            return (False, err)
        return (True, "")
    
    # Exports file as an svg
    # todo
    # Need to ensure building data is updated first
    def export_file (self, filename):
        print (f"Starting export in building data filename {filename}")

        bdata = self.get_values()
        
        # todo read this from GUI somehow
        scale = "OO"
        
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
        
        material_thickness = bdata["material_thickness"]
        scale_material = int(sc.reverse_scale_convert(material_thickness))
        # Set material thickness for Interlocking (class variable)
        Interlocking.material_thickness = scale_material
        # Set default etchline width
        EtchLine.global_etch_width = self.config.etch_line_width

        Wall.settings["outertype"] = bdata["outertype"]

        # Convert configuration into SVG settings for output
        svgsettings = {}
        
        # Leave some print statements in - otherwise do not know if progressing
        # Todo Future add progress bar
        print ("Creating SVG document format")

        svgsettings['docsize'] = sc.mms_to_pixels(doc_size_mm)
        svgsettings["strokewidth"] = self.config.stroke_width
        svgsettings["cutstroke"] = svgwrite.rgb(*self.config.cut_stroke)

        # Convert config colors into svgwrite values
        etch_strokes = []
        for stroke_color in self.config.etch_strokes:
            etch_strokes.append(svgwrite.rgb(*stroke_color))

        svgsettings["etchstrokes"] = etch_strokes
        svgsettings["etchfill"] = self.config.etch_fill
        svgsettings["etchaspolygon"] = self.config.etch_as_polygon
        svg = SVGOut(filename, svgsettings)

        walls = []
        for wall in self.get_walls():
            # Convert from string values to values from bdata
            walls.append(Wall(wall[0], wall[1], wall[2]))
            
        # Add roofs (loads differently but afterwards is handled as a wall)
        for roof in self.get_roofs():
            walls.append(Wall(roof[0], roof[1], roof[2]))

        for texture in self.get_textures():
            # If not area then default to entire wall
            area = []
            if 'area' in texture:
                area = texture['area']
            walls[texture["wall"]].add_texture(texture["type"], area, texture["settings"] )
            
        for feature in self.get_features():
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
            print ("Getting interlocking")
            # otherwise add
            for il in self.get_interlocking():
                # Add both primary and secondary for each entry
                # il_type has default but can add others in future
                il_type = "default"
                if "type" in il:
                    il_type = il["type"]
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
                walls[il["primary"][0]].add_interlocking(il["step"], il["primary"][1], "primary", reverse, il_type, parameters)
                reverse = ""
                if len(il["secondary"]) > 2:
                    reverse = il["secondary"][2]
                walls[il["secondary"][0]].add_interlocking(il["step"], il["secondary"][1], "secondary", reverse, il_type, parameters)
            
        print ("Creating output")   
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
            wall_num += 1
            # Print status
            print (f"{round((wall_num/num_walls) * 100)} % complete")
        print ("Data compiled - saving")
                    
        svg.save()
        
        print ("Save complete")
    
    # Sets all the data entries - used when loading a template 
    # Overwrites all data
    def set_all_data(self, data):
        # Make a copy of the data
        self.data = data.copy()
        
    # Returns the data object
    # May have missing data
    def get_all_data(self):
        return self.data
        
    # Returns top level data as a dictionary
    # Any values not set are returned as empty strings
    # Returns a new copy of the data
    def get_main_data(self):
        return_data = {}
        for key in ["name", "type", "subtype", "description"]:
            if key in self.data:
                return_data[key] = self.data[key]
            else:
                return_data[key] = ""
        return return_data
    
        
    # Defaults are things that are often changed to get different size of building
    # eg. depth, width, wall_height, roof_height, roof_depth & roof_width
    def get_defaults(self):
        return self.data["defaults"]
    
    # Typical are default values that are not normally changed even if you change shape of building
    #eg. roof_right_overlap / left / front / rear; wood_height, wood_etch
    def get_typical(self):
        return self.data["typical"]
    
    # Get number of walls roofs or both
    def num_walls(self):
        return len(self.data["walls"])

    def num_roofs(self):
        return len(self.data["roofs"])
  
    def num_walls_roofs(self):
        return self.num_walls() + self.num_roofs()
    
    # Get wall information processing tokens
    def get_walls(self):
        wall_data = []
        # No walls just return
        if (not "walls" in self.data):
            print ("No walls")
            return[]
        for wall in self.data["walls"]:
            # Basic error check for minimum number of parameters
            if (len(wall) < 2):
                wall_data.append (("Error", [[0,0],[0,0],[0,0],[0,0]], "front", [0,0]))
            # View is optional parameter 2 (default to front)
            if (len(wall) < 3 or wall[2] not in self.config.allowed_views):
                view = "front"
            else:
                view = wall[2]
            # basic check to see if parameter exists and is a list
            # does not check if if they are valid values
            if (len(wall) < 4 or type(wall[3]) != list) :
                position = default_pos
            else:
                #print (f"Position defined {wall[3]}")
                position = wall[3]
                
            #print ("Processing tokens")
            wall_data.append((wall[0], self.process_multiple_tokens(wall[1]), view, position))
        return wall_data
    
    def get_interlocking(self):
        if (not "interlocking" in self.data):
            #print ("No interlocking")
            return []
        return self.data["interlocking"]
    
    # Returns roofs after parsing tokens
    # Note that these will be just walls in future versions
    def get_roofs(self):
        roof_data = []
        if (not "roofs" in self.data):
            #print ("No roofs")
            return []
        for roof in self.data["roofs"]:
            # Basic error check for minimum number of parameters
            if (len(roof) < 2):
                roof_data.append(("Error", [[0,0],[0,0],[0,0],[0,0]], "top", [0,0]))
            # View is optional parameter 2 (default to top for roof)
            if (len(roof) < 3 or roof[2] not in self.config.allowed_views):
                view = "top"
            else:
                view = roof[2]
            # basic check to see if parameter exists and is a list
            # does not check if if they are valid values
            if (len(roof) < 4 or type(roof[3]) != list) :
                position = default_pos
            else:
                #print (f"Position defined {roof[3]}")
                position = roof[3]
                
            roof_data.append((roof[0], self.process_multiple_tokens(roof[1]), view, position))
        return roof_data
    
    def get_textures(self):
        if (not "textures" in self.data):
            #print ("No textures")
            return []
        return self.data["textures"]
    
    # Returns as a copy of the parameters and settings
    def get_values(self):
        values = self.data["parameters"].copy()
        # If any settings then add those
        if "settings" in self.data.keys():
            values.update(self.data["settings"])
        return values

    def get_features(self):
        if not "features" in self.data:
            return []
        return self.data["features"]
    
    def get_settings(self):
        if not "settings" in self.data:
            return []
        return self.data["settings"]
    
    # Returns the roof overlap values as a dict
    def get_roof_overlap(self):
        # Check each entry exists, otherwise return 0 as the value
        overlap_dict = {}
        if "roof_right_overlap" in self.data["parameters"].keys():
            overlap_dict["right"] = self.data["parameters"]["roof_right_overlap"]
        else:
            overlap_dict["right"] = 0
        if "roof_left_overlap" in self.data["parameters"].keys():
            overlap_dict["left"] = self.data["parameters"]["roof_left_overlap"]
        else:
            overlap_dict["left"] = 0
        if "roof_front_overlap" in self.data["parameters"].keys():
            overlap_dict["front"] = self.data["parameters"]["roof_front_overlap"]
        else:
            overlap_dict["front"] = 0
        if "roof_rear_overlap" in self.data["parameters"].keys():
            overlap_dict["rear"] = self.data["parameters"]["roof_rear_overlap"]
        else:
            overlap_dict["rear"] = 0
        return overlap_dict