# History class is used to track activities, allowing for undo (and possibly redo)


class History():
    def __init__(self, gui=None):
        self.gui = gui
        # Log all activities in this session
        # activity list grows as activites are performed
        # pos tracks the position of the next entry
        # if an undo is performed then the next add will remove future entries
        # Ie. allow any number of undo and redo but if new entry added then canno redo
        # future activities
        self.activity = []
        self.activity_pos = 0
        # set file changed to False when start or file saved
        # Any changes then set to True
        self.file_changed = False
        
    # A reset is called when loading a file - all history data is lost
    def reset(self):
        self.activity = []
        self.activity_pos = 0
        self.file_changed = False
        
    # Adds a history instance to allow undo / redo
    # Title is a user friendly title (typically action perhaps with additional name of wall or similar)
    # action is what the action type is (limited set of actions - see undo method for list)
    # old_parameters are what was there before this change (undo)
    # new_parameters is what this change does (redo)
    def add(self, title, action, old_parameters, new_parameters):
        print (f"Adding history {title} : {action}")
        self.file_changed = True
        # If there are items after the index position remove them
        while (len(self.activity) > self.activity_pos):
            self.activity.pop()
        self.activity.append(Activity(title, action, old_parameters, new_parameters))
        self.activity_pos += 1
        # If GUI known then send signal to update menu
        if self.gui != None:
            self.gui.undo_menu_signal.emit(action)
        
    # Call this when file saved to reset file_changed 
    def file_save(self):
        self.file_changed = False
        
    # Undo last change from history list
    def undo(self):
        print (f"Undoing activity {self.activity[self.activity_pos -1].title}")
        # Call appropriate method based on action type
        this_activity = self.activity[self.activity_pos -1]
        if this_activity.action == "Add wall" or this_activity.action == "Copy wall":
            print (f"Deleting wall {this_activity.title}")
            self.gui.builder.delete_wall(this_activity.old_parameters["new_wall"], history=False)
        elif this_activity.action == "Delete wall":
            print (f"Restoring wall {this_activity.title}")
            self.gui.builder.restore_wall(this_activity.old_parameters, history=False)
        elif this_activity.action == "Edit wall": # wall properties
            print (f"Restoring wall properties {this_activity.title}")
            self.gui.builder.restore_wall_properties(this_activity.old_parameters, history=False)
        elif this_activity.action == "Change texture":
            print (f"Restoring texture properties {this_activity.title}")
            wall = this_activity.new_parameters['wall']
            wall.restore_texture(this_activity.new_parameters['texture'], this_activity.old_parameters, history=False)
        elif this_activity.action == "Add feature":
            print ("Deleting feature")
            wall = this_activity.old_parameters['wall']
            wall.del_feature_obj (this_activity.old_parameters['feature'], history=False)
        elif this_activity.action == "Del feature":
            print (f"Restoring feature {this_activity.title}")
            this_activity.old_parameters['wall'].restore_feature (this_activity.old_parameters, history=False)
            # Need to update scene to regenerate object
            self.gui.update_current_scene()
        elif this_activity.action == "Move feature":
            print (f"Restoring feature position {this_activity.title}")
            this_activity.old_parameters['feature'].move((this_activity.old_parameters['min_x'],this_activity.old_parameters['min_y']))
            
        # move the activity counter back down
        self.activity_pos -= 1
        # Update the undo menu
        next_undo = ""
        if self.activity_pos > 0:
            next_undo = self.activity[self.activity_pos -1].action       
        self.gui.undo_menu_signal.emit(next_undo)
        self.gui.update_views_signal.emit()
        
class Activity():
    def __init__(self, title, action, old_parameters, new_parameters):
        self.title = title               # Description (for user)
        self.action = action             # Function to apply action
        self.old_parameters = old_parameters # Dictionary with old params (undo)
        self.new_parameters = new_parameters # Dictionary with new params (redo)
        