# Draws the view onto the scene for editing walls
# Pulls in relevant objects from builder (eg. walls) and then uses ObjViews to draw
# Created as a sub class of ViewScene
from builder import Builder
from wall import Wall
from texture import Texture
from feature import Feature
from objview import ObjView
from viewscene import ViewScene

class EditScene(ViewScene):
    def __init__(self, scene, builder, gconfig, view_name):
        super().__init__(scene, builder, gconfig, view_name)
        
       
    # Clear scene and then add walls
    def update(self):
        self.scene.clear()
        self.add_walls()
        
    # Add wall (not plural as in the viewscene
    # Takes object to add
    def add_wall(self, wall):
        # Here
        pass
        
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
            
