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
        # We can only have one wall but must be added using edit_wall
        self.wall = None
        
       
    # Clear scene and then add walls
    def update(self):
        self.scene.clear()
        self.add_walls()
        
    # Add wall to edit
    # Takes object to edit, removes existing objects and replaces with this
    # must be called before using this - otherwise we have an empty screen
    def edit_wall(self, wall):
        self.wall = wall
        self.update()
        
    # Add wall adds the wall (and components) to the scene
    # Used to update
    def add_walls(self):
        # If wall not set then return
        if self.wall == None:
            print ("No wall to edit")
            return
        
        # override existing objs - set the wall obj as the first item
        # whereas other scenes have multiple walls which are groups, this uses
        # multiple objects representing features
        # textures are handled separately *** todo ***
        self.objs = [self.wall]
        self.obj_views = [ObjView(self.scene, self.gconfig, coords = [0,0])]
        # just get cuts related to wall
        # param is optional (whether to display interlocking)
        cuts = self.wall.get_wall_cuts(self.gconfig.checkbox['il'])
        for cut in cuts:
            self.obj_views[0].add_cut(cut)
        # Add texture if enabled
        if self.gconfig.checkbox['texture']:
        #    for texture in self.wall.get_textures():
        #        for etch in texture.get_etches():
        #            self.obj_views[0].add_etch(etch)
            for etch in self.wall.get_texture_etches():
                self.obj_views[0].add_etch(etch)
                
            
        # Add features
        for feature in self.wall.get_features():
            self.objs.append(feature)
            # Does the coords need to be updated?
            self.obj_views.append(ObjView(self.scene, self.gconfig, coords = [0,0]))
            
            # Add cuts / outers / etches to the obj_view
            cuts = feature.get_cuts()
            for cut in cuts:
                self.obj_views[len(self.obj_views)-1].add_cut(cut)
                
            outers = feature.get_outers()
            if outers != None:
                for outer in outers:
                    self.obj_views[len(self.obj_views)-1].add_outer(outer)
            
            etches = feature.get_etches()
            if etches != None:
                for etch in etches:
                    self.obj_views[len(self.obj_views)-1].add_etch(etch)
            

        
    # Add walls to the scene
    def _old_add_walls(self):
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
            
