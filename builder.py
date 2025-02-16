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

# If threadpool provided then that can be used - otherwise threadpool = None and operations run sequentially
# Must be a QObject so that can use signals
class Builder(QObject):
    
    # Used during loading of wall (includes progress)
    wall_load_signal = Signal(int)
    wall_load_all_signal = Signal()
    # Used during normal refresh
    wall_update_status_signal = Signal() # Update status 
    wall_update_signal = Signal(int)
    
    def __init__(self, lcconfig, threadpool=None, gui=None):
        super().__init__()
        self.config = lcconfig
        self.threadpool = threadpool	# If threads available pass threadpool
        self.gui = gui					# If call from gui pass mainwindow for sending notifications
        
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
        self.wall_load_all_signal.connect (self.wall_load_all_received)
        self.wall_update_status_signal.connect(self.wall_update_status)
        self.wall_update_signal.connect (self.wall_update_received)
        
        # Used as part of thread to provide status
        self.current_status = 0
        # How much to add to status as each wall complete
        self.status_per_wall = 0
        
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
            #print ("File loaded - processing data")
            self.process_data()
        else:
            print ("File load failed")
        #print (f"Walls are {self.walls}")
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
    def update_walls(self, interlock, texture):
        for wall in self.walls:
            wall.update(interlock, texture)
        
    # Takes a dictionary with the wall data where points is a list within the dictionary
    # Wall args are: name, points, view="front", position=[0,0]
    def add_wall(self, wall_data):
        # Todo Calculate position
        position = [0,0]
        self.walls.append(Wall(wall_data['name'], wall_data['points'], wall_data['view'], position))
        # Return wall so it can be used elsewhere
        return self.walls[-1]
        
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
            # This reorders them (see comment in add_texture in wall for more details)
            new_wall.add_texture(texture_details[1], texture_details[0], texture_details[2])
        # Do not copy interlocking (does not make sense to do so)
        
    # After loading data this converts into builder objects
    # Deletes any existing entries
    def process_data(self):
        self.current_status = 0
        self.settings = self.building.get_settings()
        if len(self.settings) > 0:
            # Add settings to the class
            for setting in self.settings.keys():
                Wall.settings[setting] = self.settings[setting]
        
        #print ("Getting main data")
        
        self.building_info = self.building.get_main_data()
        
        self.walls = []
        all_walls = self.building.get_walls()
        
        num_walls = len(all_walls)

        current_wall = 0

        for wall in all_walls:
            #self.current_status = int((current_wall/num_walls)*100)
            #print (f"Reading in walls {self.current_status}%")
            # Convert from string values to values from bdata
            self.walls.append(Wall(wall[0], wall[1], wall[2], wall[3]))
            current_wall += 1
            
        #if num_walls > 0:
        #    print ("Reading in walls 100%")
            
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
        #if num_textures > 0:
        #    print ("Applying textures 100%")
        
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
        

        # Now perform update as used non updating functions to add features / textures
        
        ## Need to change this to threaded updates
        ## Note need to use timers to periodically check on status
        ###########
        
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
            print (f"Start {datetime.now()}")
            ## Note interlock and texture are defaults - but may need to get from config in future
            #self.update_walls_td (interlock=False, texture=True, signal=self.wall_load_signal)
            self.update_walls_single_td (interlock=False, texture=True, signal=self.wall_load_all_signal)
            
        #self.current_status = 100
        #if self.gui != None:
        #    self.gui.progress_update_signal.emit(self.current_status)
    
        #print ("Builder processing data complete\n\n")
                  
    def add_il (self, primary_wall_id, primary_edge, primary_reverse, secondary_wall_id, secondary_edge, secondary_reverse, il_type, step, parameters):
        # il moved to wall and then get back as a reference so it can be added to the interlocking group
        primary_wall = self.walls[primary_wall_id]
        primary_il = primary_wall.add_interlocking(step, primary_edge, "primary", primary_reverse, il_type, parameters)
        secondary_wall = self.walls[secondary_wall_id]
        secondary_il = secondary_wall.add_interlocking(step, secondary_edge, "secondary", secondary_reverse, il_type, parameters)
        self.interlocking_groups.append(InterlockingGroup(primary_wall_id, primary_il, secondary_wall_id, secondary_il))
        #self.print_il()
            
            
    def print_il (self):
        print (f"IL entries:")
        for il_group in self.interlocking_groups:
            print (f" {il_group}")
            
    def delete_wall (self, wall):
        for i in range (0, len(self.walls)):
            if self.walls[i] == wall:
                #print (f"Deleting wall {i}")
                # Delete any interlocking objects that reference this wall
                # Must be before deleting wall as walls renumbered afterwards
                self.delete_wall_il(i)
                # Delete the wall - also removes textures and features on the wall
                self.walls.pop(i)
                return
        
    # Delete interlocking objects referencing the wall ID
    # Reduce the number of all subsequent walls by 1
    def delete_wall_il(self, wall_id):
        for ilg in self.interlocking_groups:
            if ilg.primary_wall == wall_id or ilg.secondary_wall == wall_id:
                # Delete the il entries
                if ilg.primary_wall != wall_id:
                    self.walls[ilg.primary_wall].delete_il(ilg.primary_il.edge)
                if ilg.secondary_wall != wall_id:
                    self.walls[ilg.secondary_wall].delete_il(ilg.secondary_il.edge)
                # Delete the group
                self.interlocking_groups.remove(ilg)


    # update_walls_td to be replaced by update_walls_single_td
    # Note that this needs to be run in separate thread to gui otherwise app not responding
    # Due to GIL running in more than one addition thread has a negative impact on performance
    # In one particular test 37 seconds for single thread vs 47 seconds for thread per wall
    # Approx 20% slower by splitting threads
    # Possibly move to completely different process (difficult due to the data that would need to be passed)
    # or removal of GIL may improve this

    # Update walls using threadpool
    # Provide Signal as an argument to reply when each wall is done
    # Signal should accept int with the wall num (based on order in builder list)
    def update_walls_td (self, interlock, texture, signal):
        # Don't run if already running
        if self.num_updates_progress > 0:
            print ("Trying to start update when already updating - aborting")
            return
        # As this is threaded only shouldn't get this
        if self.threadpool == None:
            print ("Warning: Attempt to run in threads without a threadpool")
            # Insetad user the normal update
            self.update_walls(interlock, texture)
            return
        i = 0
        # Clear any existing workers
        self.workers = []
        for wall in self.walls:
            self.num_updates_progress += 1
            self.workers.append(BuilderWallUpdate(_thread_update_wall, wall, i, interlock, texture, signal))
            self.threadpool.start(self.workers[-1])
            print ("Threadpool started")
            i += 1
            
    # Same as update_walls_td but only use a single thread
    # Testing for performance
    def update_walls_single_td (self, interlock, texture, signal):
        # Don't run if already running
        if self.num_updates_progress > 0:
            print ("Trying to start update when already updating - aborting")
            return
        # As this is threaded only shouldn't get this
        if self.threadpool == None:
            print ("Warning: Attempt to run in threads without a threadpool")
            # Insetad user the normal update
            self.update_walls(interlock, texture)
            return
        self.num_updates_progress = 1
        self.worker = BuilderWallUpdate(_thread_update_all_walls, self.walls, interlock, texture, self.wall_update_status_signal, signal)
        self.threadpool.start(self.worker)
            
            
    ### Different methods depending upon why running update
    # If load then also update progress
    
    # Called during initial load - tracks progress
    # Wall num just used for debugging, just count number of update responses
    def wall_load_received(self, wall_num):
        print (f"Wall loaded {wall_num} of {self.num_updates_progress}")
        # Decrement number of walls in progress
        self.num_updates_progress -= 1
        # If reach zero then update complete so perform callback to mainwindow
        if self.num_updates_progress < 1:
            # Set to 100% complete (to remove progress window)
            self.gui.progress_update_signal.emit(100)
            # Tell MainWindo to refresh
            self.gui.load_complete_signal.emit()
            print (f"Complete {datetime.now()}")
            return
        # Otherwise update progress
        self.current_status += self.status_per_wall
        print (f"Updating status to {self.current_status}")
        self.gui.progress_update_signal.emit(self.current_status)
        
    # Wall num just used for debugging, just count number of update responses
    def wall_update_received(self, wall_num):
        self.num_updates_progress -= 1
        
    def wall_load_all_received (self):
        print ("All walls loaded")
        self.num_updates_progress = 0
        self.gui.progress_update_signal.emit(100)
        self.gui.load_complete_signal.emit()
        print (f"Complete {datetime.now()}")
        
    def wall_update_status(self):
        print ("Wall finished")
        self.current_status += self.status_per_wall
        print (f"Updating status to {self.current_status}")
        self.gui.progress_update_signal.emit(self.current_status)
        

# This is passed to a new worker thread
# Does not use self as called in threadpool
# Install all arguments must be sent through BuilderWallUpdate constructor
# Wall num is just a reference for callback (signal), if not relevant then
# can be set to 0
def _thread_update_wall(wall, wall_num, interlock, texture, callback=None):
    print ("Creating thread for wall")
    wall.update(interlock, texture)
    if callback != None:
        callback.emit (wall_num)

def _thread_update_all_walls(walls, interlock, texture, status_emit=None, callback=None):
    for wall in walls:
        if status_emit != None:
            status_emit.emit()
        wall.update(interlock, texture)
    if callback != None:
        callback.emit ()
    

            
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

            
