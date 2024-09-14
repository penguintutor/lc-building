# This is currently manually edited
# In future the configuration will be moved to a config file
# which will be accessed through this class

class LCConfig():
    def __init__(self): 
        # Same stroke width for all as used for laser
        self.stroke_width = 1
        # Black stroke used for cut
        self.cut_stroke = (0, 0, 0)        
        # Etch stroke now replaced with etch_strokes which has 0 to 9 different strengths
        # 0 = very light, 0 = very dark
        # Allows different etches for different features
        # Default is 5 - approx 50%
        # 10 strokes (0 to 9)
        # Typically use 3 to 7 (5 is default)
        
        # Lightburn colours from 10 to 19 - lighter to darker
        # Baed on rgb values
        self.etch_strokes = [
            (160, 0, 0),		#10
            (0, 160, 0),		#11
            (160, 160, 0),		#12
            (192, 128, 0),		#13
            (0, 160, 255),		#14
            (160, 0, 160),		#15
            (128, 128, 128),	#16
            (125, 135, 185),	#17
            (187, 119, 132),	#18
            (74, 111, 227)		#19
            ]
        # Alternative could use grey scale values - but they do not work in lightburn
        
        # don't show filled in - use fill in laser cutter
        self.etch_fill = "none"
                                     
        # Setting option (if set then a line is returned as a polygon based on etch_line_width
        # Normally want as True as Lightburn will not allow lines as etches (recommended)
        # If you prefer to edit as a line (eg. ink InkScape) then you can set to False
        # Note that the co-ordinates will be centre of the line so will be extended in all directions
        # This may have implications for overlapping 
        self.etch_as_polygon = True
        # Set width of etch lines (eg. door outside)
        # If etch as polygon True then this value moust be set
        self.etch_line_width = 10