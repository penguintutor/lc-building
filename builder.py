# Used for reading, editing and saving buildings
# Uses BuildingData to import the data and then to
# write it out, but otherwise uses internal objects to handle
from PySide6.QtCore import QRunnable, Slot, QThreadPool, Signal, QObject
from buildingdata import *
from helpers import *
from wall import Wall
from texture import Texture
from feature import Feature
from interlocking import Interlocking
from interlockinggroup import InterlockingGroup
from lcconfig import LCConfig
from datetime import datetime
from history import History
import copy
from viewscale import ViewScale

# To support history many of the methods have an optional variable history
# If it's default / true then we add history record (allow undo)
# if not then we don't add to the history eg. it's an undo

# If threadpool provided then that can be used - otherwise threadpool = None and operations run sequentially
# Must be a QObject so that can use signals
class Builder(QObject):
    
    # Used during loading of wall (includes progress)
    wall_load_signal = Signal()
    wall_update_complete_signal = Signal()
    # Used during normal refresh
    wall_update_status_signal = Signal() # Update status 
    wall_update_signal = Signal(int)
    
    def __init__(self, lcconfig, threadpool=None, gui=None):
        super().__init__()
        self.config = lcconfig
        self.threadpool = threadpool    # If threads available pass threadpool
        self.gui = gui                  # If call from gui pass mainwindow for sending notifications
        if self.gui != None:
            self.history = self.gui.history
        else:
            self.history = History()
        
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
        #self.process_data()
        
        # Following for creating wall updates on separate threads
        self.num_updates_progress = 0
        self.wall_load_signal.connect (self.wall_load_received)
        self.wall_update_complete_signal.connect (self.wall_load_received) # Uses same as wall load
        self.wall_update_status_signal.connect(self.wall_update_status)
        self.wall_update_signal.connect (self.wall_update_received)
        
        # Used as part of thread to provide status
        self.current_status = 0
        # How much to add to status as each wall complete
        self.status_per_wall = 0
        
        # This used when running a single update ## To decide if this is required
        #self.wall_update_running = False
        # ViewScale - if need to perform size conversions
        self.vs = ViewScale()
        
    # Only deletes the actual group
    def del_il_group (self, entry_id):
        del self.interlocking_groups[entry_id]

    # Loads a new file overwriting all data
    # Returns result of buildingdata load - (True/False, "Error string")
    # If GUI is set to a widget then use for status updates
    def load_file(self, filename):
        result = self.building.load_file(filename)
        # If successfully load then clear existing data and regenerate
        if result[0] == True:
            self.process_data()
        else:
            print ("File load failed")
        #print (f"Walls are {self.walls}")
        # Loaded file so reset the history
        self.history.reset()
        return result
        
    # Saves the file
    # Overwrites existing file
    # If want to confirm to overwrite check before calling this
    def save_file(self, filename):
        newdata = self.update_bdata()
        # Save details
        result = self.building.save_file(filename, newdata)
        print (f"Save completed - {result}")
        return result
    
    def update_bdata(self):
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
            
        newdata['walls'] = wall_data
        newdata['textures'] = texture_data
        newdata['features'] = feature_data
        
        # Add interlocking (not saved as part of wall)
        il_data = []
        # Get wall and edge from both, but other parameters from primary only (should be the same)
        for il_group in self.interlocking_groups:
            primary_entry = [il_group.primary_wall, il_group.primary_il.edge]
            # type is taken from primary entry
            il_type = il_group.primary_il.il_type
            if il_group.primary_il.reverse == True:
                primary_entry.append("reverse")
            secondary_entry = [il_group.secondary_wall, il_group.secondary_il.edge]
            if il_group.secondary_il.reverse == True:
                secondary_entry.append("reverse")
            il_data.append({
                "primary": primary_entry,
                "secondary": secondary_entry,
                "type": il_type,
                "step": il_group.primary_il.step,
                "start": il_group.primary_il.start
                })
        newdata['interlocking'] = il_data
        return newdata

        
    # Exports the file as SVG
    # Overwrites existing file
    # If want to confirm to overwrite check before calling this
    def export_file(self, filename):
        # create newdata dictionary with all current data
        newdata = self.update_bdata()
        result = self.building.export_file(filename, newdata)
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
    # interlock and texture no longer used
    def update_walls(self, interlock=False, texture=False):
        for wall in self.walls:
            wall.update()
        
    # Takes a dictionary with the wall data where points is a list within the dictionary
    # Wall args are: name, points, view="front", position=[0,0]
    def add_wall(self, wall_data, history=True):
        #print (f"Add Wall - points {wall_data['points']}")
        # Todo Calculate position
        
        # Which scene is the wall being added to
        scene_name = wall_data['view' ]
        #print (f"Scene name is {scene_name}")
        # Scene is
        scene = self.gui.view_scenes[scene_name]
        # Gets dimension of the current scene
        # min_x, min_y, max_x, max_y
        info = scene.scene_info()
        # Gets number of objecs in the current scene
        num_objs = scene.num_objs()
        
        # Calculate position avoiding existing objects
        # If not other objects then position is 0,0
        if num_objs < 1:
            position = [0,0]
        # If just one object then add next to existing
        if num_objs < 2:
            # end position of the existing object will be same as the total image
            position = [info[2] + self.gui.gconfig.default_object_spacing, 0]
        else:
            position = [0,0]
            # get size from points (size is wall size - not graphics object size)
            wall_size = self._get_size_points(wall_data['points'])
            # convert to scale
            scale_size = self.vs.convert(wall_size)
            #print (f"Scale size {scale_size}")
            position = scene.find_space(scale_size)
            
        self.walls.append(Wall(wall_data['name'], wall_data['points'], wall_data['view'], position))
        # New params are the steps required to repeat this (redo)
        # A copy of the dictionary 
        new_params = wall_data.copy()
        # Old params are the steps to undo (link to the wall object)
        old_params = {"new_wall" : self.walls[-1]}
        self.history.add(f"Add wall {wall_data['name']}", "Add wall", old_params, new_params)
        # Return wall so it can be used elsewhere
        return self.walls[-1]
    
    # Get size from points
    # This is based on one corner being 0,0 - so just find highest x and y pos
    def _get_size_points (self, points):
        x_max = 0
        y_max = 0
        for point in points:
            if point[0] > x_max:
                x_max = point[0]
            if point[1] > y_max:
                y_max = point[1]
        return [x_max, y_max]
    
    # Restores wall properties from an undo property change
    def restore_wall_properties(self, wall_data, history=False):
        # Find this wall
        for wall in self.walls:
            if wall == wall_data["wall"]:
                wall.name = wall_data["name"]
                wall.points = copy.deepcopy(wall_data["points"])
                wall.view = wall_data["view"]
                # If wall dimensions changed then also need to update any textures
                wall.update_texture_points()
                # Update this wall
                self.update_wall_td(wall, complete_signal=self.gui.update_views_signal)
                break
        
    # Restores wall from an undo request
    def restore_wall(self, wall_data, history=False):
        self.walls.append(wall_data)
        
    # Finds next appropriate name when copying by adding (x) - eg. "Wall name (1)"
    # other more efficient ways, but unlikely this will be a performance issue
    # This assumes copy of original file - ie. if copy of copy then will be "Wall name (1) (1)" etc.
    def _copy_wall_name (self, name):
        # start with 1
        update_num = 1
        # Loop forever (break when confirmed name is stored in new_name)
        while 1:
            # Add update_num and then check to see if this matches any existing names
            test_name = f"{name} ({update_num})"
            duplicate_name = False
            for wall in self.walls:
                if wall.name == test_name:
                    # indicate this is a duplicate
                    duplicate_name = True
                    break
            if duplicate_name == True:
                update_num += 1
                continue
            # if not a duplidate then test_name is valid
            return test_name
            
                
        
    def copy_wall(self, wall_to_copy, history=True):
        #print ("Copy Wall")
        
        # This is how we find space for the wall
        # First find size of the new wall (from existing wall)
        # Then search for space using  find_space (after converting to GUI dimensions)
        # get size from points (size is wall size - not graphics object size)
        wall_size = self._get_size_points(wall_to_copy.points)
        #print (f"Wall size is {wall_size}")
        
        # What scene are we adding to (same as exising object)
        scene_name = wall_to_copy.view
        #print (f"Scene name is {scene_name}")
        scene = self.gui.view_scenes[scene_name]
        
        # convert to scale
        scale_size = self.vs.convert(wall_size)
        position = scene.find_space(scale_size)
        
        
        # Copy the wall object (excluding features etc. - do that afterwards)
        new_wall_name = self._copy_wall_name(wall_to_copy.name)
        #print (f"Old name {wall_to_copy.name} - New {new_wall_name}")
        self.walls.append(Wall(new_wall_name, wall_to_copy.points, wall_to_copy.view, position))
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
            # This reorders them (see comment in add_texture in wall for more details)
            new_wall.add_texture(texture_details[1], texture_details[0], texture_details[2])
        new_params = {"copy_of" : wall_to_copy}
        old_params = {"new_wall" : new_wall}
        if history == True:
            self.history.add(f"Copy wall {new_wall.name}", "Copy wall", old_params, new_params)
        # Do not copy interlocking (does not make sense to do so)
        return new_wall
        
    # After loading data this converts into builder objects
    # Deletes any existing entries
    def process_data(self):
        #print ("**Processing Data")
        self.current_status = 0
        self.settings = self.building.get_settings()
        if len(self.settings) > 0:
            # Add settings to the class
            for setting in self.settings.keys():
                Wall.settings[setting] = self.settings[setting]
        
        self.building_info = self.building.get_main_data()
        
        self.walls = []
        all_walls = self.building.get_walls()
        
        num_walls = len(all_walls)

        current_wall = 0

        for wall in all_walls:
            # Convert from string values to values from bdata
            self.walls.append(Wall(wall[0], wall[1], wall[2], wall[3]))
            current_wall += 1
                       
        # Current status is percentage complete
        self.current_status = 2
        if self.gui != None:
            #self.gui.update_progress(self.current_status)
            self.gui.progress_update_signal.emit(self.current_status)
        
        # Add roofs (loads differently but afterwards is handled as a wall)
        for roof in self.building.get_roofs():
            # These are to be replaced in future so does not include the same % complete updates
            #print ("Adding roof")
            self.walls.append(Wall(roof[0], roof[1], roof[2], roof[3]))
            
        textures = self.building.get_textures()
        num_textures = len(textures)
        current_texture = 0
        for texture in textures:
            self.current_status = int((current_texture/num_textures)*100)
            #print (f"Applying textures {self.current_status}%")
            # If not area then default to entire wall
            area = []
            if 'area' in texture:
                area = texture['area']
            self.walls[texture["wall"]].add_texture_towall(texture["type"], area, texture["settings"] )
            current_texture += 1
        
        self.current_status = 5
        if self.gui != None:
            self.gui.progress_update_signal.emit(self.current_status)
        
        features = self.building.get_features()
        num_features = len(features)
        current_feature = 0
        for feature in features:
            self.current_status = int((current_feature/num_features)*100)
            #print (f"Adding features {self.current_status}%")
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
            
        self.current_status = 10
        if self.gui != None:
            self.gui.progress_update_signal.emit(self.current_status)
        
        # Although there is a setting to ignore interlocking still load it here to preserve
        for il in self.building.get_interlocking():
            # Great interlocking group which tracks these in case they are edited
            # Also add both primary and secondary walls for each entry
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
            primary_wall = il["primary"][0]
            # il moved to wall and then get back as a reference so it can be added to the interlocking group
            # primary_il = Interlocking(il["step"], il["primary"][1], "primary", reverse, il_type, parameters)
            primary_il = self.walls[il["primary"][0]].add_interlocking(il["step"], il["primary"][1], "primary", reverse, il_type, parameters)
            reverse = ""
            if len(il["secondary"]) > 2:
                reverse = il["secondary"][2]
            secondary_wall = il["secondary"][0]
            #secondary_il = Interlocking(il["step"], il["secondary"][1], "secondary", reverse, il_type, parameters)
            secondary_il = self.walls[il["secondary"][0]].add_interlocking(il["step"], il["secondary"][1], "secondary", reverse, il_type, parameters)
            self.interlocking_groups.append(InterlockingGroup(primary_wall, primary_il, secondary_wall, secondary_il))
        
        self.current_status = 20
        if self.gui != None:
            self.gui.progress_update_signal.emit(self.current_status)
               
        num_walls = len(self.walls)
            
        # If no walls then stop here
        if num_walls < 1:
            self.current_status = 100
            if self.gui != None:
                self.gui.progress_update_signal.emit(self.current_status)
                self.gui.load_complete_signal.emit()
            return
        
        self.current_status = 20
        self.status_per_wall = 80 / num_walls
        
        #print ("** Starting updates")

        # If not thread then use this
        if self.threadpool == None:
            
            current_wall = 0
            for wall in self.walls:
                self.current_status = int((current_wall/num_walls)*100)
                wall.update()
                self.current_status += self.status_per_wall
                if self.gui != None:
                    self.gui.progress_update_signal.emit(self.current_status)
                current_wall += 1
        else:
            # Call threaded version of update
            self.update_walls_td (status_signal=self.wall_update_status_signal, complete_signal=self.wall_load_signal)
            

    def add_il (self, primary_wall_id, primary_edge, primary_reverse, secondary_wall_id, secondary_edge, secondary_reverse, il_type, step, parameters, history=True):
        #print ("Adding IL")
        # il moved to wall and then get back as a reference so it can be added to the interlocking group
        primary_wall = self.walls[primary_wall_id]
        primary_il = primary_wall.add_interlocking(step, primary_edge, "primary", primary_reverse, il_type, parameters)
        secondary_wall = self.walls[secondary_wall_id]
        secondary_il = secondary_wall.add_interlocking(step, secondary_edge, "secondary", secondary_reverse, il_type, parameters)
        self.interlocking_groups.append(InterlockingGroup(primary_wall_id, primary_il, secondary_wall_id, secondary_il))
        #self.print_il()
        if history == True:
            # New parameters are redo - how we create if we ever needed to recreate it
            # Currently store same as old_params - may need to review this when implementing redo
            new_params = {
                'primary_wall_id': primary_wall_id,
                'primary_edge': primary_edge,
                'primary_reverse': primary_reverse,
                'secondary_wall_id': secondary_wall_id,
                'secondary_edge': secondary_edge,
                'secondary_reverse': secondary_reverse,
                'il_type': il_type,
                'step': step,
                'parameters': parameters
                }
            # Old parameters are used for undo (ie. what would we delete)
            old_params = {
                'il_group': self.interlocking_groups[-1]
                }
            self.history.add(f"Add IL", "Add IL", old_params, new_params)
        # update both the walls
        primary_wall.update_cuts()
        secondary_wall.update_cuts()
        self.gui.update_all_views()
            
    def print_il (self):
        print (f"IL entries:")
        for il_group in self.interlocking_groups:
            print (f" {il_group}")
            
    # Deletes il entries and group based on just group
    # used by undo
    def del_il_complete(self, il_group):
        wall2 = self.walls[il_group.secondary_wall]
        il2 = il_group.secondary_il
        wall2.il.remove(il2)
        # update the wall cuts
        wall2.update_cuts()
        wall1 = self.walls[il_group.primary_wall]
        il1 = il_group.primary_il
        wall1.il.remove(il1)
        wall1.update_cuts()
        # Remove group last (otherwise can't get details)
        for this_group in self.interlocking_groups:
            if this_group == il_group:
                self.interlocking_groups.remove(this_group)
            
    # Delete the wall
    # firest remove any interlocking objects relating to other walls
    # then remove the actual interlocking groups
    # Remove the wall
    # then updating any remaining interlocking groups that relate to this wall or later (decrement by one)
    def delete_wall (self, wall, history=True):
        for i in range (0, len(self.walls)):
            if self.walls[i] == wall:
                #print (f"Deleting wall {i}")
                # Delete any interlocking objects that reference this wall
                # Must be before deleting wall as walls renumbered afterwards
                self.delete_wall_il(i)
                # Delete the wall - also removes textures and features on the wall
                self.walls.pop(i)
                new_params = {}
                old_params = wall
                if history == True:
                    self.history.add(f"Delete wall {wall.name}", "Delete wall", old_params, new_params)
                # Update any il by removing any that refer to i (should not be any left)
                # Then decrement any later ones by one
                self.update_wall_ilg_delete_wall(i)
                return
           
    # This needs to be called after any walls are removed
    # If a wall is removed then it changes the numbering of the walls as storted in the ilgs
    # this decrements any subsequent wall_ids by one
    # Does nothing for this particular wall_id - that should already have been removed
    def update_wall_ilg_delete_wall(self, wall_id):
        for ilg in self.interlocking_groups:
            if ilg.primary_wall > wall_id:
                ilg.primary_wall -= 1
            if ilg.secondary_wall > wall_id:
                ilg.secondary_wall -= 1
        
    # Delete interlocking objects (including group) referencing the wall ID
    # Does not update the other groups - delete_wall_ilg needs to be called after this
    def delete_wall_il(self, wall_id, history=True):
        old_params = {}
        new_params = {}
        for ilg in self.interlocking_groups:
            if ilg.primary_wall == wall_id or ilg.secondary_wall == wall_id:
                # new parameters are used for redo - how we delete this il if asked to again
                new_params["wall_id"] = wall_id
                # Old parameters used for undo - how we undo delete (recreate)
                # Parameters required for:
                #add_il (self, primary_wall_id, primary_edge, primary_reverse, secondary_wall_id, secondary_edge, secondary_reverse, il_type, step, parameters):
                old_params["primary_wall_id"] = ilg.primary_wall
                old_params["primary_edge"] = ilg.primary_il.edge
                old_params["primary_reverse"] = ilg.primary_il.reverse
                old_params["secondary_wall_id"] = ilg.secondary_wall
                old_params["secondary_edge"] = ilg.secondary_il.edge
                old_params["secondary_reverse"] = ilg.secondary_il.reverse
                # Get other params from primary wall il
                old_params["il_type"] = ilg.primary_il.il_type
                old_params["step"] = ilg.primary_il.step
                old_params["parameters"] = ilg.primary_il.parameters
                
                if history == True:
                    self.history.add(f"Delete Wall IL", "Delete Wall IL", old_params, new_params)
                # Delete the il entries from the other walls (the wall with wall_id will be completely removed with the ILs)
                if ilg.primary_wall != wall_id:
                    #print (f"Deleting from primary {self.walls[ilg.primary_wall].name}") 
                    self.walls[ilg.primary_wall].delete_il(ilg.primary_il.edge)
                    # Update wall - there is a chance we could call this multiple times but rare that a wall would
                    # have multiple interlocks with another wall that is being deleted
                    self.update_wall_td(self.walls[ilg.primary_wall], complete_signal=self.gui.update_views_signal)
                if ilg.secondary_wall != wall_id:
                    #print (f"Deleting from secondary {self.walls[ilg.secondary_wall].name}")
                    self.walls[ilg.secondary_wall].delete_il(ilg.secondary_il.edge)
                    # Update wall - there is a chance we could call this multiple times but rare that a wall would
                    # have multiple interlocks with another wall that is being deleted
                    self.update_wall_td(self.walls[ilg.secondary_wall], complete_signal=self.gui.update_views_signal)
                # Delete the group
                self.interlocking_groups.remove(ilg)
        
        
    # update_walls_td replaced with a single thread version
    # Note that this needs to be run in separate thread to gui otherwise app not responding
    # Due to GIL running in more than one addition thread has a negative impact on performance
    # Approx 20% slower by splitting threads
    # Possibly move to completely different process (difficult due to the data that would need to be passed)
    # or removal of GIL may improve this

    # Update walls using threadpool
    # Provide Signal as an argument to reply when each wall is done
    def update_walls_td (self, status_signal, complete_signal):
        # Don't run if already running
        if self.num_updates_progress > 0:
            print ("Trying to start update when already updating - aborting")
            return
        # As this is threaded only shouldn't get this
        if self.threadpool == None:
            print ("Warning: Attempt to run in threads without a threadpool")
            # Insetad use the normal update
            self.update_walls()
            return
        self.num_updates_progress = 1
        self.worker = BuilderWallUpdate(_thread_update_all_walls, self.walls, status_signal, complete_signal)
        self.threadpool.start(self.worker)
            
    # Update a single wall
    # status is optional as delay is not as long as all windows
    # likely won't update (unless add intermediate checks)
    def update_wall_td (self, wall, status_signal=None, complete_signal=None):
        # run this update regardless of any existing updates in progress
        # this is only called from gui so don't check for threadpool - it must exist
        wall_worker = BuilderWallUpdate(_thread_update_wall, wall, 0, status_signal, complete_signal)
        self.threadpool.start(wall_worker)
        
    ### Different methods depending upon why running update
    # If load then also update progress
    
    # Wall num just used for debugging, just count number of update responses
    def wall_update_received(self, wall_num):
        self.num_updates_progress -= 1
        
    # Finished loading wall
    def wall_load_received (self):
        self.num_updates_progress = 0
        self.gui.progress_update_signal.emit(100)
        self.gui.load_complete_signal.emit()
        
    # One wall has finished loading so update status
    def wall_update_status(self):
        self.current_status += self.status_per_wall
        self.gui.progress_update_signal.emit(self.current_status)
        

# This is passed to a new worker thread
# Does not use self as called in threadpool
# Install all arguments must be sent through BuilderWallUpdate constructor
# Wall num is just a reference for callback (signal), if not relevant then
# can be set to 0
def _thread_update_wall(wall, wall_num, status_emit=None, complete_emit=None):
    wall.update()
    # Update status and complete separately allows sometimes to use progress bar, but not always
    if status_emit != None:
        status_emit.emit (wall_num)
    if complete_emit != None:
        complete_emit.emit ()

# Update all the walls
def _thread_update_all_walls(walls, status_emit=None, complete_emit=None):
    for wall in walls:
        # Send status update as each wall is complete
        if status_emit != None:
            status_emit.emit()
        wall.update()
    # Send complete when all updates complete
    if complete_emit != None:
        complete_emit.emit ()
    

            
# Create a seperate worker class for adding walls - so that they are on separate threads           
class BuilderWallUpdate (QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        
    @Slot() # Pyside6.QtCore.Slot
    def run(self):
        self.fn(*self.args, **self.kwargs)

            
