# Draws the view onto the scene - eg. front walls
# Pulls in relevant objects from builder (eg. walls) and then uses ObjViews to draw
from PySide6.QtCore import Signal, QObject
from objview import ObjView

class ViewScene(QObject):
    
    update_scene_signal = Signal()
    
    def __init__(self, main_window, scene, builder, gconfig, view_name):
        super().__init__()
        self.gui = main_window
        self.scene = scene
        self.builder = builder
        self.gconfig = gconfig
        self.view_name = view_name
        
        self.update_scene_signal.connect(self.update)
        
        # obj are any objects to manipulate (typically wall objects from builder)
        # which can be used to interact with the wall
        # obj_views is a representation of the object on the screen
        # Need to keep index in sync, so if remove from one need to remove from other as well
        self.objs = []
        self.obj_views = []
        
    # Get information about the objects on the viewscene
    def scene_info (self):
        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0
        print ("Getting information")
        for i in range(0,len(self.obj_views)):
            # Get position / dimensions
            pos = self.obj_views[i].get_pos()
            size = self.obj_views[i].get_size()
            bounding = self.obj_views[i].get_bounding()
            #size = self.objs[i].get_size_string()
            #print (f"Object {i} - pos {pos}, size {size} = {bounding}")
            if bounding[0] < min_x:
                min_x = bounding[0]
            if bounding[2] > max_x:
                max_x = bounding[2]
            if bounding[1] < min_y:
                min_y = bounding[1]
            if bounding[3] > max_y:
                max_y = bounding[3]
        # Get screen area in use
        print (f"Current region {min_x}, {min_y}, {max_x}, {max_y}")
        return [min_x, min_y, max_x, max_y]
        
    # Finds space on screen for an object size
    # If no space in existing then add after existing objects
    # aim for ratio of 8x6 
    def find_space (self, size):
        current_screen = self.scene_info()
        # These are temp values for tracking
        start_x = current_screen[0]
        start_y = current_screen[1]
        end_x = current_screen[2]
        end_y = current_screen[3]
        
        current_x = start_x
        current_y = start_y
        next_y_position = None
        while (current_y < end_y - size[1]):
            #print (f"Y pos {current_y}")
            while (current_x < end_x - size[0]):
                #print (f"  X pos {current_x}")
                overlap_result = self._check_overlap(current_x, current_y, size[0], size[1])
                # If no overlap then return this as a valid space
                if overlap_result == None:
                    return [current_x, current_y]
                # otherwise increment the x_position of the current pos, and potentially the next to try y
                current_x = overlap_result[0] + self.gconfig.default_object_spacing
                if next_y_position == None or next_y_position > overlap_result[1]:
                    next_y_position = overlap_result[1]
                # this will result in the next_y_position being the smallest of any objects that conflict with the current row being checked
            # finished this row - move down to the next one
            current_x = 0
            # If we didn't update y then none found on this row
            if next_y_position == None:
                break
            current_y = next_y_position + self.gconfig.default_object_spacing
            # reset to only detect on this row
            next_y_position = None
        # If not returned no space found
        # So place on right or bottom as appropriate
        # Works out roughly for an 8 x 6 - if width lower than put on right
        # otherwise put on bottom
        #print (f"Extending screen - {current_screen}")
        if current_screen[2] / 8 < current_screen[3] / 6:
            new_pos = [current_screen[2] + self.gconfig.default_object_spacing, 0]
            #print (f"Adding horizontally {new_pos}")
            return new_pos
        else:
            new_pos = [0, current_screen[3] + self.gconfig.default_object_spacing]
            #print (f"Adding vertically {new_pos}")
            return new_pos
        
        
    # checks all objects in viewscene for overlapping rectangle bounds
    # if overlap then return right_x and bottom_y of object that overlaps
    # returning the first object that it overlaps with
    # the calling can then increment x based on the current - or store y (to keep lowest) to try next loop 
    def _check_overlap (self, x, y, size_x, size_y):
        for this_obj in self.obj_views:
            this_obj_coords = this_obj.get_bounding()
            # Test if rects overlap
            # Simple version of seperating axis theorem https://code.tutsplus.com/collision-detection-using-the-separating-axis-theorem--gamedev-169t
            # if the right of this object is to the left of the new
            if this_obj_coords[2] < x:
                continue
            # if the left of this object is to the right of the new
            if this_obj_coords[0] > x+size_x:
                continue
            # if the bottom of this object is above the new
            if this_obj_coords[3] < y:
                continue
            # if the top of this object is below the new
            if this_obj_coords[1] > y+size_y:
                continue
            # if reach here then we have a collision - so return this object x / y last position
            return [this_obj_coords[2], this_obj_coords[3]]
        # otherwise none overlap so return None
        return None
        
    def num_objs (self):
        return len(self.obj_views)
        
       
    # Clear scene and then add walls
    # Full update / vs partial update - not needed on scene
    # but allowed to set full=True - no difference
    def update(self):
        #print ("View update")
        #print (f"Update view scene {self.view_name}")
        self.update_obj_pos()
        self.scene.clear()
        self.objs = []
        self.obj_views = []
        self.add_walls()
        
    # Deletes the object view and the object
    def del_obj_by_id (self, id):
        del self.objs[id]
        del self.obj_views[id]
        
    # For each of the objects get current pos from obj view and update feature
    # This is based on view position - so is absolute co-ordinates
    # No need to convert to mm etc.
    def update_obj_pos(self):
        for i in range (0, len(self.objs)):
            #print (f"Updating {self.objs[i]} pos {self.obj_views[i].pos}")
            self.objs[i].move_pos(self.obj_views[i].pos)

        
    # searches for obj view and returns the corresponding objs
    # ie. from view object get the builder object (eg. wall)
    def get_obj_from_obj_view(self, selected_obj):
        for i in range (0, len(self.obj_views)):
            if self.obj_views[i].item_group == selected_obj:
                #print (f"*** This object found - obj {i}")
                # objs is the actual object (e.g. wall)
                #print (f" which is {self.objs[i].name}")
                return (self.objs[i])
        return (None)
    
    # searches for obj view and returns the corresponding id
    # ie. from view object get the builder object (eg. wall)
    def get_id_from_obj_view(self, selected_obj):
        for i in range (0, len(self.obj_views)):
            if self.obj_views[i].item_group == selected_obj:
                return i
        return None
    
    # Not implemented - possible cleanup
    #def del_obj_from_obj_view(self, selected_obj):
    #    id = self.get_id_from_obj_view(selected_obj)
        
        
    # Add walls to the scene
    def add_walls(self):
        if self.gconfig.debug > 2:
            print ("Debug - View Scene {self.scene} add walls")
        # Delete old objects and add new
        #print ("View Scene Add walls")
        # Get all the walls from builder
        walls = self.builder.get_walls_view(self.view_name)
        #print (f"Adding {len(walls)} walls")
        for wall in walls:
            self.objs.append (wall)
            # Create objview to abstract out the drawing
            # Uses lasercutter config lcconfig - could have heirarchical in future - allow override for graphics display
            # Note currently put at 0,0 - this will overwrite need to work out positioning
            #self.obj_views.append(ObjView(self.scene, self.gconfig, coords = wall.position))
            self.obj_views.append(ObjView(self.scene, self.gconfig))
            # position using setPos
            
            # Now draw them on the scene
            # Etches first, then outers then walls - this then shows overlap in that order
            # Also typically will want to output in that order (although that is under control of laser cut software)

            # Get the etching
            etches = wall.get_etches(self.gconfig.checkbox['il'], self.gconfig.checkbox['texture'])
            if etches != None:
                for etch in etches:
                    self.obj_views[-1].add_etch(etch)
                    
            # Get the outers (show different pen)
            outers = wall.get_outers(self.gconfig.checkbox['il'], self.gconfig.checkbox['texture'])
            if outers != None:
                for outer in outers:
                    self.obj_views[-1].add_outer(outer)
                    
            cuts = wall.get_cuts(self.gconfig.checkbox['il'], self.gconfig.checkbox['texture'])
            for cut in cuts:
                self.obj_views[-1].add_cut(cut)
            
            # Set position after adding graphics items
            #print (f"Setting {wall} to {wall.position}")
            self.obj_views[-1].set_pos(wall.position)

 
                    
    def clear(self):
        self.scene.clear()
            
