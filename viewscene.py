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
        self.obj_views = [] 
        
       
    # Currently just add_walls, but in future may need to clear existing
    def update(self):
        self.scene.clear()
        self.add_walls()
        
    def add_walls(self):
        #print ("Add walls")
        # Get all the walls from builder
        walls = self.builder.get_walls_view(self.view_name)
        #print (f"Adding {len(walls)} walls")
        for wall in walls:
            # Create objview to abstract out the drawing
            # Uses lasercutter config lcconfig - could have heirarchical in future - allow override for graphics display
            # Note currently put at 0,0 - this will overwrite need to work out positioning
            self.obj_views.append(ObjView(self.scene, self.builder.config, coords = [0,0]))
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
            
