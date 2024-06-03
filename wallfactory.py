# Wall Factory class
# Implements Factory Method Pattern using object classes

from wall import *

class WallFactory:
    _creators = {
        "WallRect" : WallRect,
        "WallApex" : WallApex,
        "RoofApexLeft" : RoofApexLeft,
        "RoofApexRight" : RoofApexRight,
        "RoofFlat" : RoofFlat
        }
        
    @staticmethod
    def create_wall(type, args):
        creator = WallFactory._creators[type]
        return creator(*args)