# History class is used to track activities, allowing for undo (and possibly redo)


class History():
    def __init__(self):
        # Log all activities in this session
        self.activity = []
        self.activity_pos = 0
        # set file changed to False when start or file saved
        # Any changes then set to True
        self.file_changed = False
        
    def add(self, title, action, old_parameters, new_parameters):
        self.file_changed = True
        self.activity.append(Activity(title, action, old_parameters, new_parameters))
        self.activity_pos += 1
        
    # Call this when file saved to reset file_changed 
    def file_save(self):
        self.file_changed = False
        
class Activity():
    def __init__(self, title, action, old_parameters, new_parameters):
        self.title = title               # Description (for user)
        self.action = action             # Function to apply action
        self.old_parameters = old_parameters # Dictionary with old params (undo)
        self.new_parameters = new_parameters # Dictionary with new params (redo)
        