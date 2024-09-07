#Gui config

# This is currently manually edited
# In future the configuration will be moved to a config file
# which will be accessed through this class

# Changes are normally saved whenever changed in the GUI settings
# For example resize and that will be default size when next starts

class GConfig():
    def __init__(self, status):
        self.maximized = True
        self.default_screensize = [1000, 700]
        
        # Check to see if default screensize is a reasonable size for this screen
        # just basic check to see if it's larger and if so set to maximum screen size
        # May still be too bit (does not allow for application bars / launchers) but
        # at least managable 
        if self.default_screensize[0] > status['screensize'][0]:
            self.default_screensize[0] = status['screensize'][0]
        if self.default_screensize[1] > status['screensize'][1]:
            self.default_screensize[1] = status['screensize'][1]
