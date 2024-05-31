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
        
    @staticmethod
    def create_etch(type, args, io):
        creator = LaserFactory._etch_creators[type]
        return creator(*args, io)
    
    
    @staticmethod
    def create_cut(type, args, io):
        creator = LaserFactory._cut_creators[type]
        return creator(*args, io)