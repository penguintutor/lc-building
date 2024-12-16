# Draws the view onto the scene - eg. front walls
# Pulls in relevant objects from builder (eg. walls) and then uses ObjViews to draw
from builder import Builder
from wall import Wall
from texture import Texture
from feature import Feature
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
    def update(self):
        self.scene.clear()
        self.add_walls()
        
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
        
    # Add walls to the scene
    def add_walls(self):
        #print ("Add walls")
        # Get all the walls from builder
        walls = self.builder.get_walls_view(self.view_name)
        #print (f"Adding {len(walls)} walls")
        for wall in walls:
            self.objs.append (wall)
            # Create objview to abstract out the drawing
            # Uses lasercutter config lcconfig - could have heirarchical in future - allow override for graphics display
            # Note currently put at 0,0 - this will overwrite need to work out positioning
            self.obj_views.append(ObjView(self.scene, self.gconfig, coords = wall.position))
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
 
                    
    def clear(self):
        self.scene.clear()
            
