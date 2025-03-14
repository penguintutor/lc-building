# History class is used to track activities, allowing for undo (and possibly redo)


class History():
    def __init__(self, gui=None):
        self.gui = gui
        # Log all activities in this session
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
        
    def add(self, title, action, old_parameters, new_parameters):
        print (f"Adding history {title} : {action}")
        self.file_changed = True
        self.activity.append(Activity(title, action, old_parameters, new_parameters))
        self.activity_pos += 1
        # If GUI known then send signal to update menu
        if self.gui != None:
            self.gui.undo_menu_signal.emit(action)
        
    # Call this when file saved to reset file_changed 
    def file_save(self):
        self.file_changed = False
        
class Activity():
    def __init__(self, title, action, old_parameters, new_parameters):
        self.title = title               # Description (for user)
        self.action = action             # Function to apply action
        self.old_parameters = old_parameters # Dictionary with old params (undo)
        self.new_parameters = new_parameters # Dictionary with new params (redo)
        