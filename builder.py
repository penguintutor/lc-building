# Used by mainwindow and lcmake to provide single
# file for accessing tools


import config

class Builder():
    
    def __init__(self, config):
        self.config = config
