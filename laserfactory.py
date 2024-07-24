# Laser Factory class
# Implements Factory Method Pattern using object classes
from laser import *

class LaserFactory:
    _etch_creators = {
        "line" : EtchLine,
        "rect" : EtchRect,
        "polygon" : EtchPolygon
        }
    
    _cut_creators = {
        "line" : CutLine,
        "rect" : CutRect,
        "polygon" : CutPolygon
        }
    
    _outer_creators = {
        "line" : OuterLine,
        "rect" : OuterRect,
        "polygon" : OuterPolygon
        }
        
    @staticmethod
    def create_etch(type, args, io, strength=5):
        creator = LaserFactory._etch_creators[type]
        # special case for polygon need to keep args as a list
        if type == "polygon":
            return creator(args, io, strength)
        else:
            return creator(*args, io, strength)
    
    @staticmethod
    def create_cut(type, args, io):
        creator = LaserFactory._cut_creators[type]
        return creator(*args, io)
    
    @staticmethod
    def create_outer(type, args, io):
        creator = LaserFactory._outer_creators[type]
        return creator(*args, io)