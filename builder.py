# Used for reading, editing and saving buildings
# Uses BuildingData to import the data and then to
# write it out, but otherwise uses internal objects to handle


from buildingdata import *
from helpers import *
from wall import Wall
from texture import Texture
from feature import Feature
from interlocking import Interlocking
from lcconfig import LCConfig

class Builder():
    def __init__(self, lcconfig):
        self.config = lcconfig
        
        # Create empty building data instance - can load or edit
        self.building = BuildingData(self.config)
        
        # Create instance of self.walls
        self.walls = []
        self.process_data()

    # Loads a new file overwriting all data
    # Returns result of buildingdata load - (True/False, "Error string")
    def load_file(self, filename):
        result = self.building.load_file(filename)
        # If successfully load then clear existing data and regenerate
        if result[0] == True:
            self.process_data()
        return result
        
    # Saves the file
    # Overwrites existing file
    # If want to confirm to overwrite check before calling this
    def save_file(self, filename):
        #Todo update building at this point
        
        
        ####***************************####
        
        # eg. position of walls
        return self.building.save_file(filename)
        
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
        
    # Takes a dictionary with the wall data where points is a list within the dictionary
    # Wall args are: name, points, view="front", position=[0,0]
    def add_wall(self, wall_data):
        # Todo Calculate position
        position = [0,0]
        self.walls.append(Wall(wall_data['name'], wall_data['points'], wall_data['view'], position)) 
        
    # After loading data this converts into builder objects
    # Deletes any existing entries
    def process_data(self):
        
        print ("\n\nBuilder processing data")
        settings = self.building.get_settings()
        if len(settings) > 0:
            # Add settings to the class
            for setting in settings.keys():
                Wall.settings[setting] = settings[setting]
        
        #    print ("Settings loaded")
        #else:
        #    print ("No settings")
        
        self.walls = []
        all_walls = self.building.get_walls()
        for wall in all_walls:
        #    print ("Loading Wall")
            # Convert from string values to values from bdata
            self.walls.append(Wall(wall[0], wall[1], wall[2], wall[3]))
        
        # Add roofs (loads differently but afterwards is handled as a wall)
        for roof in self.building.get_roofs():
        #    print (f"Roof {roof}")
            self.walls.append(Wall(roof[0], roof[1], roof[2], roof[3]))
            
        for texture in self.building.get_textures():
            # If not area then default to entire wall
            area = []
        #    print (" Adding texture")
            if 'area' in texture:
                area = texture['area']
            self.walls[texture["wall"]].add_texture(texture["type"], area, texture["settings"] )
        

        for feature in self.building.get_features():
        #    print ("Adding feature")
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
                
            self.walls[feature["wall"]].add_feature(pos, polygon,
                                               feature["cuts"], feature["etches"], feature["outers"])
            
        #print ("End feature")
            
        # Although there is a setting to ignore interlocking still load it here to preserve
        for il in self.building.get_interlocking():
        #    print ("Adding interlocking")
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
            self.walls[il["primary"][0]].add_interlocking(il["step"], il["primary"][1], "primary", reverse, parameters)
            reverse = ""
            if len(il["secondary"]) > 2:
                reverse = il["secondary"][2]
            self.walls[il["secondary"][0]].add_interlocking(il["step"], il["secondary"][1], "secondary", reverse, parameters)
    
        print ("Builder processing data complete\n\n")