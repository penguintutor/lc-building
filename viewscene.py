# Draws the view onto the scene - eg. front walls
# Pulls in relevant objects from builder (eg. walls) and then uses ObjViews to draw
from objview import ObjView

class ViewScene():
    def __init__(self, scene, builder, gconfig, view_name):
        self.scene = scene
        self.builder = builder
        self.gconfig = gconfig
        self.view_name = view_name
        # obj are any objects to manipulate (typically wall objects from builder)
        # which can be used to interact with the wall
        # obj_views is a representation of the object on the screen
        # Need to keep index in sync, so if remove from one need to remove from other as well
        self.objs = []
        self.obj_views = []
        
       
    # Clear scene and then add walls
    # Full update / vs partial update - not needed on scene
    # but allowed to set full=True - no difference
    def update(self, full=True):
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
            etches = wall.get_etches()
            if etches != None:
                for etch in etches:
                    self.obj_views[len(self.obj_views)-1].add_etch(etch)
                    
            # Get the outers (show different pen)
            outers = wall.get_outers()
            if outers != None:
                for outer in outers:
                    self.obj_views[len(self.obj_views)-1].add_outer(outer)
                    
            cuts = wall.get_cuts()
            for cut in cuts:
                self.obj_views[len(self.obj_views)-1].add_cut(cut)
            
            # Set position after adding graphics items
            #print (f"Setting {wall} to {wall.position}")
            self.obj_views[len(self.obj_views)-1].set_pos(wall.position)
            #self.obj_views[len(self.obj_views)-1].item_group.setPos(QPoint(*wall.position))
            #print (f"New posion {self.obj_views[len(self.obj_views)-1].item_group.pos()}")
 
                    
    def clear(self):
        self.scene.clear()
            
