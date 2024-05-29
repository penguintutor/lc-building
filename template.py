import json


# Parent level template
class Template ():
    
    def __init__ (self):
        # Start with template = "None" - update when loaded
        self.name = "None"
        self.json_data = {}
        pass
    
    def load_template (self, filename):
        self.filename = filename
        with open(filename, 'r') as templatefile:
            self.json_data = json.load(templatefile)
        
    # Returns a copy of the data so it can be edited without changing actual template
    # To update template then update the instance of this class rather than the data copy
    def get_data (self):
        return self.json_data.copy()
        
    # Save using existing filename (eg. update template)
    def save_template (self):
        self.saveas_template(self.filename)
        
    def saveas_template (self, filename):
        # set to new name
        self.filename = filename
        with open(filename, 'w') as templatefile:
            json.dump(self.json_data, templatefile)
        