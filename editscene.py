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
    
    def __init__(self, main_window, scene, builder, gconfig, view_name):
        super().__init__(main_window, scene, builder, gconfig, view_name)
        # We can only have one wall but must be added using edit_wall
        self.wall = None
        
        
    # Perform full update using thread and then callback to update
    #def update_full(self):
        # check for moved objeects
    #    self.update_feature_pos()
    #    self.builder.update_wall_td(self.wall, complete_signal=self.update_scene_signal)
    
    # Call when finished editing to update the wall then tell the new
    # viewscene to update itself
    def update_switch(self, new_scene):
        self.builder.update_wall_td(self.wall, complete_signal=new_scene.update_scene_signal)
       
    # Clear scene and then add wall
    # Tried removing objects but risk of chase condition where
    # object deleted but tries to be read - this is slower but safer to
    # always do a full update
    # feature_obj_pos is when moving features elsewhere (eg. align)
    # instead of use the object_view pos - use the actual pos configured in the feature
    # normally do not want to override this
    # Selection is default which indicates that those that were selected should still be
    # If any objects have been deleted then it should be set to false becaues otherwise
    # will try and select objects that are deleted.
    def update(self, feature_obj_pos=False, selection=True):
        #print ("Updating edit scene")
        # check for moved objeects
        if feature_obj_pos == True:
            # Update view based on feature details
             self.update_pos_feature()   
        else:
            # Update feature details based on view
            self.update_feature_pos()
        if selection == True:
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
        if selection == True:
            # reselect those that should be selected
            for i in selected_features:
                # check if selected_feature still exists - if not then ignore
                self.obj_views[i].item_group.setSelected(True)

        
    ## For each of the features get current pos from obj view and update feature
    # When moving a feature then it is relative to the wall (which is at 0,0),
    # and we need to convert to mm before applying to object
    def update_feature_pos(self, history=True):
        # Avoid problem where object becomes unselected after move
        # Store selected objects, then restore which are selected
        # Get list of selected features so we can reselect them after update
        selected_features = []
        for i in range (1, len(self.obj_views)):
            if self.obj_views[i].item_group.isSelected():
                selected_features.append(self.obj_views[i].item_group)
        #print (f"Selected items {selected_features}")
                
        for i in range (1, len(self.objs)):
            view_new_pos = self.obj_views[i].pos
            # If not moved then ignore
            if view_new_pos[0] == 0 and view_new_pos[1] == 0:
                continue
            # convert view pos to mm pos
            view_new_pos = Laser.vs.reverse_convert(view_new_pos)
            if history == True:
                # old_parameters are what was there before this change (undo)
                old_params = {
                    'feature': self.objs[i],
                    'min_x': self.objs[i].min_x,
                    'min_y': self.objs[i].min_y
                    }
            self.objs[i].move_rel(view_new_pos)
            if history == True:
                # new_parameters is what this change does (redo)
                new_params = {
                    'feature': self.objs[i],
                    'min_x': self.objs[i].min_x,
                    'min_y': self.objs[i].min_y
                    }        
                # Store current position in history
                self.gui.history.add(f"Move feature {self.objs[i].template}", "Move feature", old_params, new_params)
        #print (f"Selected objs after move {selected_features}")
        # unselect all features
        for this_object in self.obj_views:
            this_object.item_group.setSelected(False)
        # reselect those that should be selected
        for this_group in selected_features:
            this_group.setSelected(True)
            
    # This is the opposite of update_feature_pos
    # Looks at the feature and updates the obj_views to reflect the updated values
    # this is used when feature position moved by code (eg. align)
    def update_pos_feature(self):
        #print ("Updating position")
        for i in range (1, len(self.objs)):
            pos = self.objs[i].get_pos()
            #print (f"Current feature {i} pos {pos}")
            obj_pos = Laser.vs.convert(pos)
            #print (f"Setting pos feature {i} to {obj_pos}")
            self.obj_views[i].set_pos(obj_pos)
        
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
            for etch in self.wall.get_texture_etches_basic():
                self.obj_views[0].add_etch(etch)
        #print (f"Wall pos is {self.obj_views[0].get_pos()}")
            
    def add_features (self):
        # Add features
        for feature in self.wall.get_features():
            self.objs.append(feature)
            # coords is the start of the wall
            self.obj_views.append(ObjView(self.scene, self.gconfig, coords = [0,0]))
            
            ### Add background to the feature - this is specific to the edit scene for
            # performance as the entire background is shown
            exclude = feature.get_exclude()
            # Add exclude as a polygon
            self.obj_views[-1].add_exclude(exclude)
            
            # Add cuts / outers / etches to the obj_view
            cuts = feature.get_cuts()
            for cut in cuts:
                self.obj_views[-1].add_cut(cut)
                
            outers = feature.get_outers()
            if outers != None:
                for outer in outers:
                    self.obj_views[-1].add_outer(outer)
            
            etches = feature.get_etches()
            if etches != None:
                for etch in etches:
                    self.obj_views[-1].add_etch(etch)
 
                    
    def clear(self):
        self.scene.clear()
            