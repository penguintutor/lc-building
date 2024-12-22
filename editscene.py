# Draws the view onto the scene for editing walls
# Pulls in relevant objects from builder (eg. walls) and then uses ObjViews to draw
# Created as a sub class of ViewScene
from builder import Builder
from wall import Wall
from texture import Texture
from feature import Feature
from objview import ObjView
from viewscene import ViewScene
from laser import Laser

class EditScene(ViewScene):
    def __init__(self, scene, builder, gconfig, view_name):
        super().__init__(scene, builder, gconfig, view_name)
        # We can only have one wall but must be added using edit_wall
        self.wall = None
        
       
    # Clear scene and then add wall
    def update(self):
        # check for moved objeects
        self.update_feature_pos()
        # clear scene
        self.scene.clear()
        # add wall and features
        self.add_wall()
        
    # For each of the features get current pos from obj view and update feature
    def update_feature_pos(self):
        for i in range (1, len(self.objs)):
            view_new_pos = self.obj_views[i].new_pos
            if view_new_pos != (0,0):
                # convert view pos to mm pos
                view_new_pos = Laser.vs.reverse_convert(view_new_pos)
                self.objs[i].move_rel(view_new_pos)
        
    # Add wall to edit
    # Takes object to edit, removes existing objects and replaces with this
    # must be called before using this - otherwise we have an empty screen
    def edit_wall(self, wall):
        self.wall = wall
        self.update()
        
    # Add wall adds the wall (and components) to the scene
    # Used to update
    def add_wall(self):
        # If wall not set then return
        if self.wall == None:
            print ("No wall to edit")
            return
        
        # override existing objs - set the wall obj as the first item
        # whereas other scenes have multiple walls which are groups, this uses
        # multiple objects representing features
        # textures are handled separately *** todo ***
        self.objs = [self.wall]
        # Create a view object, but set it not moveable
        self.obj_views = [ObjView(self.scene, self.gconfig, coords = [0,0], moveable=False)]
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
                
        #print (f"Wall pos is {self.obj_views[0].get_pos()}")
                
        print ("* Adding Features")
        # Add features
        for feature in self.wall.get_features():
            print (f"Adding wall feature {feature}")
            self.objs.append(feature)
            # coords is the start of the wall
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
                    
        print (f"Feature pos is {self.obj_views[1].get_pos()}")
 
                    
    def clear(self):
        self.scene.clear()
            