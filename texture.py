# Texture is an etch applied to a wall (or similar)
# Not shown where conflict with a feature (eg. window)
# Creates an instance for each element - then can use to detect
# if it needs to be removed because of other features

# Only work in mm
# Wall should handle conversion to pixels


class Texture():
    # 4 points needed to create a bounding rectangle
    # used for quick collission detection 
    def __init__ (self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        
    # detcect if collide with a feature and if so remove those parts of the etch
    def collide_feature (self, feature_min_x, feature_min_y, feature_max_x, feature_max_y):
        pass
    
    
# must be parallel top and bottom
# Provide 4 points starting top left going clockwise
class TrapezoidTexture(Texture):
    def __init__ (self, points):
        # calc max bounding box
        # start with first point and then look for larger / smaller as required
        min_x = points[0][0]
        max_x = points[0][0]
        min_y = points[0][1]
        max_y = points[0][1]
        for point in points:
            if point[0] < min_x:
                min_x = point[0]
            if point[0] > max_x:
                max_x = point[0]
            if point[1] < min_y:
                min_y = point[1]
            if point[1] > max_y:
                max_y = point[1]
        super().__init__ (min_x, min_y, max_x, max_y)
        self.points = points
    
    # Return a list even if only one element
    def get_etches(self):
        # convert to polygon
        # Add start to end
        new_points = self.points.copy()
        new_points.append(self.points[0])
        return [("polygon", new_points)]
    
    
# start is x, y - dimension w, l
# Do not use negative dimensions - start must be top left
class RectTexture(Texture):
    def __init__ (self, start_pos, dimension):
        super().__init__(start_pos[0], start_pos[1], start_pos[0]+dimension[0], start_pos[1]+dimension[1])
        self.start_pos = start_pos
        self.dimension = dimension
    
    # Return a list even if only one element
    def get_etches(self):
        return [("rect", (self.start_pos[0], self.start_pos[1]), (self.dimension[0], self.dimension[1]))]
    