# Used for reading, editing and saving buildings
# Uses BuildingData to import the data and then to
# write it out, but otherwise uses internal objects to handle


from buildingdata import *
from helpers import *
from wall import Wall
from texture import Texture
from feature import Feature
from interlocking import Interlocking
from interlockinggroup import InterlockingGroup
from lcconfig import LCConfig

class Builder():
    def __init__(self, lcconfig):
        self.config = lcconfig
        
        # Create empty building data instance - can load or edit
        self.building = BuildingData(self.config)
        
        self.building_info = {}
        
        # Create instance of self.walls
        self.walls = []
        # Also need to track interlocking features seperately
        # Note interlocking is based on order of self.walls - so if change
        # walls (eg. delete a wall) then need to update the walls in interlocking
        # including remove interlocking that relies on that wall (primary and secondary)
        self.interlocking_groups = []
        self.process_data()

    # Loads a new file overwriting all data
    # Returns result of buildingdata load - (True/False, "Error string")
    def load_file(self, filename):
        result = self.building.load_file(filename)
        # If successfully load then clear existing data and regenerate
        if result[0] == True:
            print ("File loaded - processing data")
            self.process_data()
        else:
            print ("File load failed")
        return result
        
    # Saves the file
    # Overwrites existing file
    # If want to confirm to overwrite check before calling this
    def save_file(self, filename):
        # create newdata dictionary with all current data
        # Start with building summary information (main data) which is a dictionary
        newdata = self.building_info
        newdata['settings'] = self.settings
        
        wall_data = []
        texture_data = []
        feature_data = []
        
        wall_num = 0
        for wall in self.walls:
            #print ("Getting walls")
            wall_data.append(wall.get_save_data())
            #print ("Getting textures")
            textures = wall.get_save_textures(wall_num)
            #print (f"Textures are {textures}")
            for texture in textures:
                texture_data.append (texture)
            #print ("Getting Features")
            features = wall.get_save_features(wall_num)
            #print (f"Features are {features}")
            for feature in features:
                feature_data.append (feature)
            wall_num += 1
            
        #print ("Adding data")
        newdata['walls'] = wall_data
        newdata['textures'] = texture_data
        newdata['features'] = feature_data
        
        # Add interlocking (not part of wall)
        il_data = []
        # Get wall and edge from both, but other parameters from primary only (should be the same)
        for il_group in self.interlocking_groups:
            primary_entry = [il_group.primary_wall, il_group.primary_il.edge]
            if il_group.primary_il.reverse == True:
                primary_entry.append("reverse")
            secondary_entry = [il_group.secondary_wall, il_group.secondary_il.edge]
            if il_group.secondary_il.reverse == True:
                secondary_entry.append("reverse")
            il_data.append({
                "primary": primary_entry,
                "secondary": secondary_entry,
                "step": il_group.primary_il.step,
                "start": il_group.primary_il.start
                })
        newdata['interlocking'] = il_data
                
        #print (f"New data:\n {newdata}")
        # Save details
        result = self.building.save_file(filename, newdata)
        print (f"Save completed - {result}")
        return result
        
    # Exports the file as SVG
    # Overwrites existing file
    # If want to confirm to overwrite check before calling this
    def export_file(self, filename):
        # create newdata dictionary with all current data
        # Not perform anymore - instead need to update current data into building data
        # Start with building summary information (main data) which is a dictionary
#         newdata = self.building_info
#         newdata['settings'] = self.settings
#         
#         wall_data = []
#         texture_data = []
#         feature_data = []
#         
#         wall_num = 0
#         for wall in self.walls:
#             #print ("Getting walls")
#             wall_data.append(wall.get_save_data())
#             #print ("Getting textures")
#             textures = wall.get_save_textures(wall_num)
#             #print (f"Textures are {textures}")
#             for texture in textures:
#                 texture_data.append (texture)
#             #print ("Getting Features")
#             features = wall.get_save_features(wall_num)
#             #print (f"Features are {features}")
#             for feature in features:
#                 feature_data.append (feature)
#             wall_num += 1
#             
#         #print ("Adding data")
#         newdata['walls'] = wall_data
#         newdata['textures'] = texture_data
#         newdata['features'] = feature_data
#         
#         # Add interlocking (not part of wall)
#         il_data = []
#         # Get wall and edge from both, but other parameters from primary only (should be the same)
#         for il_group in self.interlocking_groups:
#             primary_entry = [il_group.primary_wall, il_group.primary_il.edge]
#             if il_group.primary_il.reverse == True:
#                 primary_entry.append("reverse")
#             secondary_entry = [il_group.secondary_wall, il_group.secondary_il.edge]
#             if il_group.secondary_il.reverse == True:
#                 secondary_entry.append("reverse")
#             il_data.append({
#                 "primary": primary_entry,
#                 "secondary": secondary_entry,
#                 "step": il_group.primary_il.step,
#                 "start": il_group.primary_il.start
#                 })
#         newdata['interlocking'] = il_data
#                 
#         #print (f"New data:\n {newdata}")
#         # Save details
#         result = self.building.export_file(filename, newdata)
        result = self.building.export_file(filename)
        return result
        
    # Get the walls that match a certain view
    def get_walls_view(self, view):
        # Create temporary list of which walls to export
        view_walls = []
        for wall in self.walls:
            #print (f"Wall view {wall.view}")
            if wall.view == view:
                #print ("Adding wall here ")
                view_walls.append(wall)
        return view_walls
    
    # Update walls - eg. if interlock or texture setting changed then reflect against all walls
    def update_walls(self, interlock, texture):
        for wall in self.walls:
            wall.update(interlock, texture)
        
    # Takes a dictionary with the wall data where points is a list within the dictionary
    # Wall args are: name, points, view="front", position=[0,0]
    def add_wall(self, wall_data):
        # Todo Calculate position
        position = [0,0]
        self.walls.append(Wall(wall_data['name'], wall_data['points'], wall_data['view'], position))
        
    def copy_wall(self, wall_to_copy):
        position = [0,0]
        # Copy the wall object (excluding features etc. - do that afterwards)
        self.walls.append(Wall(wall_to_copy.name+" (Copy)", wall_to_copy.points, wall_to_copy.view, position))
        # new_wall is the last added entry
        new_wall = self.walls[-1]
        # Copy features
        for this_feature in wall_to_copy.get_features():
            #new_wall.add_feature (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None):
            new_wall.add_feature(*(this_feature.get_entry()))
        # Copy textures
        for this_texture in wall_to_copy.get_textures():
            texture_details = this_texture.get_entry()
            # When adding texture to wall it takes different order to Texture constructor
            # Thsi reorders them (see comment in add_texture in wall for more details)
            new_wall.add_texture(texture_details[1], texture_details[0], texture_details[2])
        # Do not copy interlocking (does not make sense to do so)
        
        
    # After loading data this converts into builder objects
    # Deletes any existing entries
    def process_data(self):
        
        #print ("\n\nBuilder processing data")
        self.settings = self.building.get_settings()
        if len(self.settings) > 0:
            # Add settings to the class
            for setting in self.settings.keys():
                Wall.settings[setting] = self.settings[setting]
        
        #print ("Get main info")
        self.building_info = self.building.get_main_data()
        
        #print ("Get walls")
        self.walls = []
        all_walls = self.building.get_walls()
        
        num_walls = len(all_walls)
        #print (f"Num walls {num_walls}")
        current_wall = 0
        for wall in all_walls:
            percent_loaded = int((current_wall/num_walls)*100)
            print (f"Reading in walls {percent_loaded}%")
            # Convert from string values to values from bdata
            self.walls.append(Wall(wall[0], wall[1], wall[2], wall[3]))
            current_wall += 1
            
        if num_walls > 0:
            print ("Reading in walls 100%")
        
        # Add roofs (loads differently but afterwards is handled as a wall)
        for roof in self.building.get_roofs():
            # These are to be replaced in future so does not include the same % complete updates
            #print ("Adding roof")
            self.walls.append(Wall(roof[0], roof[1], roof[2], roof[3]))
            
        textures = self.building.get_textures()
        num_textures = len(textures)
        current_texture = 0
        for texture in textures:
            percent_loaded = int((current_texture/num_textures)*100)
            print (f"Applying textures {percent_loaded}%")
            # If not area then default to entire wall
            area = []
            if 'area' in texture:
                area = texture['area']
            self.walls[texture["wall"]].add_texture_towall(texture["type"], area, texture["settings"] )
            current_texture += 1
        if num_textures > 0:
            print ("Applying textures 100%")
        
        features = self.building.get_features()
        num_features = len(features)
        current_feature = 0
        for feature in features:
            percent_loaded = int((current_feature/num_features)*100)
            print (f"Adding features {percent_loaded}%")
            # Features takes a polygon, but may be represented as more basic rectangle.
            pos = feature["parameters"]["pos"]
            polygon = []
            # If no points provided then convert rectangle into a polygon
            if ("exclude" in feature["parameters"].keys()):
                # Updated how these are calculated should now be relative to start position
                for this_point in feature["parameters"]["exclude"]:
                    polygon.append((this_point[0], this_point[1]))
            else:
                width = feature["parameters"]["width"]
                height = feature["parameters"]["height"]
                polygon = rect_to_polygon((0,0), width, height)
                
            self.walls[feature["wall"]].add_feature_towall(feature["type"], feature["template"], pos, polygon,
                                               feature["cuts"], feature["etches"], feature["outers"])
            current_feature += 1
        if num_features > 0:
            print (f"Adding features 100%")
        
            
        # Although there is a setting to ignore interlocking still load it here to preserve
        for il in self.building.get_interlocking():
        #    print ("Adding interlocking")
            # Great interlocking group which tracks these in case they are edited
            # Also add both primary and secondary walls for each entry
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
            primary_wall = il["primary"][0]
            primary_il = Interlocking(il["step"], il["primary"][1], "primary", reverse, parameters)
            self.walls[il["primary"][0]].add_interlocking(il["step"], il["primary"][1], "primary", reverse, parameters)
            reverse = ""
            if len(il["secondary"]) > 2:
                reverse = il["secondary"][2]
            secondary_wall = il["secondary"][0]
            secondary_il = Interlocking(il["step"], il["secondary"][1], "secondary", reverse, parameters)
            self.walls[il["secondary"][0]].add_interlocking(il["step"], il["secondary"][1], "secondary", reverse, parameters)
            self.interlocking_groups.append(InterlockingGroup(primary_wall, primary_il, secondary_wall, secondary_il))
        
        # Now force update as used non updating functions to add features / textures
        num_walls = len(self.walls)
        current_wall = 0
        for wall in self.walls:
            percent_loaded = int((current_wall/num_walls)*100)
            print (f"Rendering walls {percent_loaded}%")
            wall.update()
            current_wall += 1
        if num_walls > 0:
            print ("Rendering walls 100%")
    
        #print ("Builder processing data complete\n\n")
            
    def delete_wall (self, wall):
        for i in range (0, len(self.walls)):
            if self.walls[i] == wall:
                print (f"Deleting wall {i}")
                # todo - delete the wall, delete other objects that reference this wall
                # including interlocking (remove any direct and update any others to refer to new wall numbers)
                # delete any textures and features that are applied to this wall
                return
        