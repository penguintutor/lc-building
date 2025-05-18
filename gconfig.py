#Gui config
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

# This is currently manually edited
# In future the configuration will be moved to a config file
# which will be accessed through this class

# Changes are normally saved whenever changed in the GUI settings
# For example resize and that will be default size when next starts

class GConfig():
    def __init__(self, status):
        self.maximized = False
        self.default_screensize = [1000, 700]
        
        # Use for debugging
        # 0 = no debugging
        # 1 = main actions / windows
        # 2 = more detailed
        # 4 = very high level of debug
        self.debug = 0
        
        # Check to see if default screensize is a reasonable size for this screen
        # just basic check to see if it's larger and if so set to maximum screen size
        # May still be too bit (does not allow for application bars / launchers) but
        # at least managable 
        if self.default_screensize[0] > status['screensize'][0]:
            self.default_screensize[0] = status['screensize'][0]
        if self.default_screensize[1] > status['screensize'][1]:
            self.default_screensize[1] = status['screensize'][1]
            
        self.pen_cut = QPen(QColor(0,0,0), 2)
        # Etch is 0 to 9
        # Note that Blue is always set high to give a blue tint
        self.pen_etch_colors = [
            QColor(250, 250, 255),
            QColor(225, 225, 255),
            QColor(200, 200, 255),
            QColor(175, 175, 255),
            QColor(150, 150, 255),
            QColor(125, 125, 255),
            QColor(100, 100, 255),
            QColor(75, 75, 255),
            QColor(50, 50, 255),
            QColor(25, 25, 255)
            ]
        self.pen_etch = []
        for this_color in self.pen_etch_colors:
            self.pen_etch.append(QPen(this_color, 1))
        
        self.pen_outer = QPen(Qt.green, 1)
        
        self.pen_highlight = QPen(QColor(255,0,0))
        self.pen_highlight.setWidth(3)
        
        # Same a lcconfig setting about etch as polygon, but instead
        # based on view
        # Normally don't want this set
        self.view_etch_as_polygon = False
        
        # temporary settings - based on checkbox settings from mainwindow
        # il is Interlocking (whether to display or not)
        self.checkbox = {
            'il': False,
            'texture': True
            }
