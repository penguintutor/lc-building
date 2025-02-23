# History class is used ot track activities, allowing for undo (and possibly redo)


class History():
    def __init__(self):
        # Log all activities in this session
        self.activity = []
        self.activity_pos = 0
        
    def add(self, title, action, old_parameters, new_parameters):
        self.activity.append(Activity(title, action, old_parameters, new_parameters))
        self.activity_pos += 1
        
class Activity():
    def __init__(self, title, action, old_parameters, new_parameters):
        self.title = title               # Description (for user)
        self.action = action             # Function to apply action
        self.old_parameters = old_parameters # Dictionary with old params (undo)
        self.new_parameters = new_parameters # Dictionary with new params (redo)
        