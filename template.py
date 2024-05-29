from abc import ABC, abstractmethod
import json
import re

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Parent level template
# Abstract class using the Abstract Base Classes 
class Template (ABC):

    # maps value to appropriate value or fields
    # Note that start is 0,0
    # (offset - either for feature in wall or wall in page) is
    # normally in wall
    static_values = {
        "x": 0,
        "y": 0,
        "startx": 0,
        "starty": 0
        }

    def __init__ (self):
        # Start with template = "None" - update when loaded
        self.name = "None"
        self.json_data = {}
        pass

    # Required method that all child classes must implement
    @abstractmethod
    def get_type(self):
        pass

    def load_template (self, filename):
        self.filename = filename
        with open(filename, 'r') as templatefile:
            self.json_data = json.load(templatefile)
    
    # Checks the appropriate predefined, defaults, parameters for a matching value_string
    # Returns as string
    def get_value_str (self, value_string):
        # if number then return directly as string
        if (is_number(value_string)):
            return (value_string)
        # pre-defined values
        if value_string in Template.static_values.keys():
            return str(Template.static_values[value_string])
        elif value_string in self.json_data["defaults"]:
            return str(self.json_data["defaults"][value_string])
        # typical is only in certain templates
        elif ("typical" in self.json_data.keys() and value_string in self.json_data["typical"]):
            return str(self.json_data["typical"][value_string])
        else:
            return None
        
            
    def process_multiple_tokens (self, token_strings):
        new_list = []
        for this_string in token_strings:
            # if this_string is actually a list then call recursively
            if type(this_string) is list:
                new_list.append(self.process_multiple_tokens (this_string))
            else:
                new_list.append(self.process_token (this_string))
        return new_list
            
    # Processes values from loaded cuts and etches looking for tokens and
    # converts the values relative to existing values
    # returns as string
    def process_token_str (self, token_string):
        new_string = ""
        # Token can be any alphanumeric and _
        # Note include numbers as token - including . for fractions
        current_pos = 0
        for m in re.finditer(r"[\w.]+", token_string):
            this_token = m.group(0)
            # replace from start
            start = m.start()
            end = m.end()
            if start > current_pos:
                new_string += token_string[current_pos:start]
            new_string += self.get_value_str(this_token)
            current_pos = end
        # Any remaining chars add to the end
        if len(token_string) > current_pos:
            new_string += token_string[current_pos:]
        return new_string
        
    # Process token and perform eval to return as a number
    def process_token (self, token_string):
        new_string = self.process_token_str(token_string)
        value = eval(new_string)
        return value
            
        
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
        
    