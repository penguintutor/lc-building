# Draws the view onto the scene - eg. front walls
# Pulls in relevant objects from builder (eg. walls) and then uses ObjViews to draw
from builder import Builder
from wall import Wall
from texture import Texture
from feature import Feature
from objview import ObjView
from zoom import Zoom

class ViewScene():
    def __init__(self, scene, builder, view_name):
        self.scene = scene
        self.builder = builder
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
            self.obj_views.append(ObjView(self.scene, self.builder.config, coords = wall.position))
            # Now draw them on the scene
            cuts = wall.get_cuts()
            for cut in cuts:
                self.obj_views[len(self.obj_views)-1].add_cut(cut)
 
            # Get the etching
            etches = wall.get_etches()
            if etches != None:
                for etch in etches:
                    self.obj_views[len(self.obj_views)-1].add_etch(etch)
                    
    def clear(self):
        self.scene.clear()
            
