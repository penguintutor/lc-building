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
        
        
    # Perform full update using thread and then callback to update
    def update_full(self):
        # check for moved objeects
        self.update_feature_pos()
        self.builder.update_wall_td(self.wall, complete_signal=self.update_scene_signal)
       
    # Clear scene and then add wall
    # Tried removing objects but risk of chase condition where
    # object deleted but tries to be read - so slower but safer to
    # always do a full update
    def update(self):
        # check for moved objeects
        #self.update_feature_pos()
        # Get list of selected features so we can reselect them after update
        selected_features = []
        for i in range (1, len(self.obj_views)):
            if self.obj_views[i].item_group.isSelected():
                selected_features.append(i)
        # clear scene
        self.scene.clear()
        # delete all views by resetting the list
        self.obj_views == []
        # add wall and features
        self.add_wall() # includes textures
        self.add_features() # Add features seperately
        # reselect those that should be selected
        for i in range(0, len(selected_features)):
            self.obj_views[i].item_group.setSelected(True)

        
    ## For each of the features get current pos from obj view and update feature
    # When moving a feature then it is relative to the wall (which is at 0,0),
    # and we need to convert to mm before applying to object
    def update_feature_pos(self):
        for i in range (1, len(self.objs)):
            view_new_pos = self.obj_views[i].pos
            # convert view pos to mm pos
            view_new_pos = Laser.vs.reverse_convert(view_new_pos)
            self.objs[i].move_rel(view_new_pos)
        
    # Add wall to edit
    # Takes object to edit, removes existing objects and replaces with this
    # must be called before using this - otherwise we have an empty screen
    def edit_wall(self, wall):
        self.wall = wall
        
    # Gets the scene that the wall is part of
    def get_wall_scene(self):
        return self.wall.view
     
    # Do not without first fixing as risk of trying to access deleted object
    # Removes the wall from the scene (potentially so it can be readded)
    # In edit view always have one wall and it's the first object_view
    #def del_wall(self, wall):
    #    # Wall is the first item
    #    self.scene.destroyItemGroup(wall.item_group)
        
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
        self.objs = [self.wall]
        # Create a view object, but set it not moveable
        # Replaces existing
        self.obj_views = [ObjView(self.scene, self.gconfig, coords = [0,0], moveable=False)]
        # just get cuts related to wall
        cuts = self.wall.get_wall_cuts(self.gconfig.checkbox['il'], self.gconfig.checkbox['texture'])
        for cut in cuts:
            self.obj_views[0].add_cut(cut)
        # Add texture if enabled
        if self.gconfig.checkbox['texture']:
            for etch in self.wall.get_texture_etches():
                self.obj_views[0].add_etch(etch)
        #print (f"Wall pos is {self.obj_views[0].get_pos()}")
            
    def add_features (self):
        # Add features
        for feature in self.wall.get_features():
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
 
                    
    def clear(self):
        self.scene.clear()
            
