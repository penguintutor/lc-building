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
    def objects_info (self):
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
            print (f"Object {i} - pos {pos}, size {size} = {bounding}")
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
            
